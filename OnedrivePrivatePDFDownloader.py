import numpy as np
import argparse
import logging
import os
import shutil
import tempfile
from PIL import Image
import io
from contextlib import contextmanager
import time
from time import sleep

import img2pdf
import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, JavascriptException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService


# if the class names are not up-to-date, you can use the browser inspector
# to get the new ones and add them here
CLASS_NAMES_TOTAL_PAGES = ["status_5a88b9b2"]
CLASS_NAMES_FILE_NAME = ["OneUpNonInteractiveCommandNewDesign_156f96ef"]
CLASS_NAMES_TOOLBAR = ["root_5a88b9b2"]
ARIA_LABELS_NEXT_PAGE = ["Vai alla pagina successiva.", "Go to the next page."]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

# avoid unnecessary logs
logging.getLogger("img2pdf").setLevel(logging.ERROR)
logging.getLogger("selenium").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("PIL").setLevel(logging.ERROR)


def parse_arguments() -> argparse.Namespace:
    """Parse the arguments from the command line.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Export a PDF (also the protected ones) from an authenticated session.",
        epilog="Made with ❤️ by @willnaoosmith and @Francesco146",
    )
    parser.add_argument(
        "--browser",
        "-b",
        type=str,
        choices=["firefox", "chrome"],
        help="Browser to use (firefox or chrome)",
        default="firefox",
        metavar="BROWSER",
    )
    parser.add_argument(
        "--profile-dir",
        "-p",
        type=str,
        help="Path to the browser profile.",
        default=None,
        metavar="PATH",
    )
    parser.add_argument(
        "--profile-name",
        "-n",
        type=str,
        help="Profile name to use, only for Chrome.",
        default=None,
        metavar="PATH",
    )
    parser.add_argument(
        "--keep-imgs",
        "-k",
        action="store_true",
        help="Keep the images after the PDF creation",
        default=False,
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Show debug messages",
        default=False,
    )
    parser.add_argument(
        "--output-file",
        "-o",
        type=str,
        help="Specify the output file name",
        required=False,
        metavar="FILE",
    )
    parser.add_argument("url", type=str, help="URL of the PDF file")
    return parser.parse_args()


def find_element(browser: webdriver, identifiers: list[str], by: By):
    """Find an element by one of the identifiers in the list.

    Args:
        browser (webdriver): Browser instance
        identifiers (list[str]): List of identifiers to search
        by (By): The method to use for finding the element

    Raises:
        NoSuchElementException: If no element is found

    Returns:
        WebElement: The found element
    """
    for identifier in identifiers:
        try:
            match by:
                case By.CLASS_NAME:
                    element = browser.find_element(by, identifier)
                case By.XPATH:
                    element = browser.find_elements(
                        by, f"//button[@aria-label='{identifier}']"
                    )[-1]
                case _:
                    raise ValueError(f"Unsupported method: {by}")
            logging.debug(f"Element found using {by}: '{identifier}'")
            return element
        except (NoSuchElementException, IndexError): # index error for the XPATH method
            logging.debug(f"Element not found using {by}: '{identifier}'")
            continue
    raise NoSuchElementException(
        f"No element found with any of the identifiers: {identifiers}"
    )


def crop_screenshot(image_path: str) -> None:
    """Crop the screenshot to remove empty space and center the content."""
    try:
        # Open the image
        img = Image.open(image_path)
        width, height = img.size

        # Convert to numpy array for analysis
        img_array = np.array(img)

        # Find content boundaries (non-white pixels)
        # Using a threshold close to white to handle anti-aliasing
        threshold = 250
        mask = (img_array < threshold).any(axis=2)

        # Find the content boundaries
        rows = mask.any(axis=1)
        cols = mask.any(axis=0)

        # Get the content boundaries
        top = np.argmax(rows)
        bottom = height - np.argmax(rows[::-1])
        left = np.argmax(cols)
        right = width - np.argmax(cols[::-1])

        # Add a small padding (10 pixels)
        padding = 10
        left = max(0, left - padding)
        right = 720 + padding # set the value of the right cropping side according to your needs
        top = max(0, top - padding)
        bottom = min(height, bottom + padding)

        # Crop the image
        cropped = img.crop((left, top, right, bottom))

        # Save the cropped image
        cropped.save(image_path, 'PNG', quality=100)
        logging.info(f"Image cropped from {width}x{height} to {right - left}x{bottom - top}")

    except Exception as e:
        logging.error(f"Failed to crop image: {str(e)}")
        # Keep original image if cropping fails


def get_browser(args) -> webdriver:
    """Get the browser instance based on the arguments with high-resolution settings."""
    options = None
    service = None

    logging.info(f"Initializing browser: '{args.browser}'")

    match args.browser:
        case "firefox":
            options = webdriver.FirefoxOptions()
            service = FirefoxService(log_path=os.devnull)
            if args.profile_dir:
                options.profile = webdriver.FirefoxProfile(args.profile_dir)
            # Set high resolution window size
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
            # Prevent browser from closing
            options.add_argument("--detach")
            browser = webdriver.Firefox(service=service, options=options)
            browser.set_window_size(1920, 1080)
            return browser

        case "chrome":
            options = webdriver.ChromeOptions()
            service = ChromeService(log_path=os.devnull)
            if args.profile_dir and args.profile_name:
                options.add_argument(f"user-data-dir={args.profile_dir}")
                options.add_argument(f"--profile-directory={args.profile_name}")
            # Set high resolution window size and device scale factor
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--force-device-scale-factor=2")
            # Prevent browser from closing
            options.add_argument("--detach")
            options.add_experimental_option("detach", True)
            browser = webdriver.Chrome(service=service, options=options)
            # Set high DPI settings using JavaScript
            browser.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': 1920,
                'height': 1080,
                'deviceScaleFactor': 2,
                'mobile': False
            })
            return browser

        case _:
            raise ValueError(f"Unsupported browser: {args.browser}")


def wait_for_canvas_load(browser: webdriver, timeout: int = 30, check_interval: float = 0.5) -> tuple[
    selenium.webdriver.remote.webelement.WebElement, int, int]:
    """Wait for the canvas to load and return it with its dimensions."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Try to find all canvases and get the visible one
            canvas_script = """
                const canvases = Array.from(document.querySelectorAll('canvas'));
                for (const canvas of canvases) {
                    const rect = canvas.getBoundingClientRect();
                    const style = window.getComputedStyle(canvas);

                    // Check if canvas is visible and rendered
                    if (rect.width > 0 && 
                        rect.height > 0 && 
                        style.display !== 'none' && 
                        style.visibility !== 'hidden' &&
                        canvas.width > 0 &&
                        canvas.height > 0) {

                        return {
                            canvas: canvas,
                            width: canvas.width,
                            height: canvas.height,
                            rect: rect
                        };
                    }
                }
                return null;
            """

            result = browser.execute_script(canvas_script)

            if result:
                canvas = browser.execute_script("return arguments[0].canvas;", result)
                return canvas, result['width'], result['height']

        except Exception as e:
            logging.debug(f"Canvas detection attempt failed: {str(e)}")

        sleep(check_interval)

    logging.error("Canvas detection timed out. Available elements on page:")
    try:
        elements = browser.execute_script("""
            return Array.from(document.querySelectorAll('*')).map(el => ({
                tag: el.tagName,
                id: el.id,
                class: el.className
            }));
        """)
        logging.error(f"Page elements: {elements}")
    except:
        pass

    raise TimeoutError("Canvas did not load within the specified timeout")


def wait_for_page_transition(browser: webdriver, timeout: int = 10) -> None:
    """Wait for page transition animation to complete."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check if any animations are running
            is_transitioning = browser.execute_script("""
                return document.querySelector('canvas').style.transform !== '';
            """)
            if not is_transitioning:
                return
        except:
            pass
        sleep(0.5)
    logging.warning("Page transition timeout reached")


def take_high_res_screenshot(browser: webdriver, image_path: str) -> None:
    """Take a high-resolution screenshot of the PDF canvas with proper cropping."""
    global original_style, original_width, original_height
    canvas = None
    try:
        # Wait for any page transition to complete
        wait_for_page_transition(browser)

        # Wait for canvas to load and get dimensions
        canvas, original_width, original_height = wait_for_canvas_load(browser)

        if not canvas:
            raise Exception("No visible canvas found")

        # Store the original canvas style and dimensions
        original_style = browser.execute_script("""
            const canvas = arguments[0];
            return {
                width: canvas.style.width,
                height: canvas.style.height,
                transform: canvas.style.transform,
                position: canvas.style.position,
                display: canvas.style.display
            };
        """, canvas)

        # Reset any existing transformations and set fixed dimensions
        browser.execute_script("""
            const canvas = arguments[0];
            // Reset all transformations and positioning
            canvas.style.transform = 'none';
            canvas.style.position = 'relative';
            canvas.style.width = arguments[1] + 'px';
            canvas.style.height = arguments[2] + 'px';

            // Set fixed dimensions for consistent capture
            canvas.width = arguments[1] * 2;  // Double for high resolution
            canvas.height = arguments[2] * 2;

            // Force layout recalculation
            canvas.getBoundingClientRect();
        """, canvas, original_width, original_height)

        # Center the canvas and hide overlays
        browser.execute_script("""
            arguments[0].scrollIntoView({block: 'start', behavior: 'instant'});
            // Hide any overlay elements
            const overlays = document.querySelectorAll('[role="toolbar"], [role="navigation"], [class*="toolbar"], [class*="overlay"]');
            overlays.forEach(el => el.style.visibility = 'hidden');
        """, canvas)

        sleep(2)  # Wait for any visual updates

        # Take screenshot of the canvas
        try:
            canvas.screenshot(image_path)
            crop_screenshot(image_path)
        except Exception as e:
            logging.error(f"Direct canvas screenshot failed: {str(e)}")
            # Fallback to canvas data URL method
            browser.execute_script("""
                const canvas = arguments[0];
                const dataUrl = canvas.toDataURL('image/png', 1.0);
                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = arguments[1];
                link.click();
            """, canvas, os.path.basename(image_path))
            sleep(1)

    except Exception as e:
        logging.error(f"Screenshot failed: {str(e)}")
        raise
    finally:
        # Restore the canvas to its original state
        if canvas:
            try:
                browser.execute_script("""
                    const canvas = arguments[0];
                    const style = arguments[1];
                    // Restore original styles
                    canvas.style.width = style.width;
                    canvas.style.height = style.height;
                    canvas.style.transform = style.transform;
                    canvas.style.position = style.position;
                    canvas.style.display = style.display;
                    // Restore original dimensions
                    canvas.width = arguments[2];
                    canvas.height = arguments[3];
                    // Restore overlay visibility
                    const overlays = document.querySelectorAll('[role="toolbar"], [role="navigation"], [class*="toolbar"], [class*="overlay"]');
                    overlays.forEach(el => el.style.visibility = '');
                """, canvas, original_style, original_width, original_height)
            except Exception as e:
                logging.warning(f"Failed to restore canvas state: {str(e)}")


def hide_toolbar(browser, class_names) -> None:
    """Hide the toolbar by one of the class names in the list.

    Args:
        browser (WebDriver): Browser instance
        class_names (list[str]): List of class names to search

    Returns:
        None
    """
    for class_name in class_names:
        try:
            browser.execute_script(
                f"document.getElementsByClassName('{class_name}')[0].style.visibility = 'hidden'"
            )
            logging.debug(f"Toolbar hidden using class name: '{class_name}'")
            return
        except (IndexError, NoSuchElementException, JavascriptException):
            logging.debug(f"Toolbar not found using class name: '{class_name}'")
            continue
    raise NoSuchElementException(
        f"No toolbar found with any of the class names: {class_names}"
    )


@contextmanager
def browser_context(args: argparse.Namespace):
    """Context manager to handle the browser session.

    Args:
        args (argparse.Namespace): Arguments from the command line

    Yields:
        webdriver: Browser instance
    """
    browser = get_browser(args)
    try:
        yield browser
    finally:
        browser.quit()
        print()  # Add a new line after the browser is finally closed
        logging.info("Browser session ended.")


def get_total_pages(browser: webdriver) -> int:
    """Get the total number of pages from the page counter or manually.

    Args:
        browser (webdriver): Browser instance

    Returns:
        int: The total number of pages
    """
    try:
        total_of_pages = int(
            find_element(browser, CLASS_NAMES_TOTAL_PAGES, By.CLASS_NAME).text.replace(
                "/", ""
            )
        )
        logging.info(f"Total number of pages detected: {total_of_pages}")
    except (ValueError, NoSuchElementException):
        logging.warning(
            "The page counter is not visible or the CLASS_NAME_TOTAL_PAGES is not up-to-date."
        )
        total_of_pages = int(input("Insert the total number of pages manually: "))
    return total_of_pages


def get_output_filename(args: argparse.Namespace, browser: webdriver) -> str:
    """Get the output filename based on the arguments, the detected one or manually.

    Args:
        args (argparse.Namespace): Arguments from the command line
        browser (webdriver): Browser instance

    Returns:
        str: The output filename
    """
    if args.output_file:
        filename = args.output_file
    else:
        try:
            filename = find_element(browser, CLASS_NAMES_FILE_NAME, By.CLASS_NAME).text
            logging.info(f"Detected file name: '{filename}'")
        except NoSuchElementException:
            logging.warning(
                "The file name is not visible or the CLASS_NAME_FILE_NAME is not up-to-date."
            )
            filename = input(
                "Insert the file name manually (with the extension e.g.: file.pdf): "
            )

    return filename

def main() -> None:
    """Main function to export the PDF file."""
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    with browser_context(args) as browser:
        browser.get(args.url)

        # Set initial window size
        browser.set_window_size(1920, 1080)
        sleep(1)  # Wait for resize

        input(
            "Make sure to authenticate and reach the PDF preview. "
            "Once the file is loaded and the page counter is visible, press [ENTER] to start. "
            "Keep the browser in the foreground for better results.\n> [ENTER] "
        )
        sleep(2)

        total_of_pages = get_total_pages(browser)
        filename = get_output_filename(args, browser)

        logging.info(
            f'Starting the export of the file "{filename}" in high resolution. '
            "This might take a while depending on the number of pages."
        )

        files_list: list[str] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                hide_toolbar(browser, CLASS_NAMES_TOOLBAR)
                logging.info("Toolbar hidden for clean screenshots.")
            except NoSuchElementException:
                logging.warning(
                    "The toolbar is not visible or the CLASS_NAME_TOOLBAR is not up-to-date. "
                    "The screenshots might contain the toolbar."
                )

            page_number = 1
            while page_number <= total_of_pages:
                sleep(5)  # Wait for page to load completely
                image_path = f"{temp_dir}/{str(page_number)}.png"

                try:
                    take_high_res_screenshot(browser, image_path)
                except NoSuchElementException as e:
                    logging.error(
                        "Cannot find the pdf within the page because of internal changes in OneDrive."
                    )
                    raise e

                files_list.append(image_path)
                logging.info(f"Page {str(page_number)} of {str(total_of_pages)} exported in high resolution.")

                page_number += 1

                try:
                    next_page_button = find_element(browser, ARIA_LABELS_NEXT_PAGE, By.XPATH)
                    browser.execute_script("arguments[0].click();", next_page_button)
                except (NoSuchElementException, JavascriptException):
                    logging.error(
                        "Cannot find the next page button. ARIA_LABEL_NEXT_PAGE might be outdated "
                        "or a race condition occurred. Saving the obtained pages."
                    )
                    break

            logging.info(f"Saving the high-resolution file as '{filename}'.")
            with open(filename, "wb") as out_file:
                out_file.write(img2pdf.convert(files_list))

            if args.keep_imgs:
                keep_dir = f"{filename}_images"
                os.makedirs(keep_dir, exist_ok=True)
                for file_path in files_list:
                    shutil.copy(file_path, keep_dir)
                logging.info(f"High-resolution images kept in directory '{keep_dir}'.")

    logging.info("Temporary images removed.")


if __name__ == "__main__":
    main()
