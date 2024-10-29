import argparse
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
from time import sleep

import img2pdf
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService

# if the class names are not up-to-date, you can use the browser inspector
# to get the new ones and add them here
CLASS_NAMES_TOTAL_PAGES = ["status_5a88b9b2"]
CLASS_NAMES_FILE_NAME = ["OneUpNonInteractiveCommandNewDesign_156f96ef"]
CLASS_NAMES_TOOLBAR = ["root_5a88b9b2"]
ARIA_LABELS_NEXT_PAGE = ["Vai alla pagina successiva."]

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
        except NoSuchElementException:
            logging.debug(f"Element not found using {by}: '{identifier}'")
            continue
    raise NoSuchElementException(
        f"No element found with any of the identifiers: {identifiers}"
    )


def get_browser(args) -> webdriver:
    """Get the browser instance based on the arguments.

    Args:
        args (argparse.Namespace): Arguments from the command line

    Raises:
        ValueError: If the browser is not supported

    Returns:
        webdriver: Browser instance
    """
    options = None
    service = None

    logging.info(f"Initializing browser: '{args.browser}'")

    match args.browser:
        case "firefox":
            options = webdriver.FirefoxOptions()
            service = FirefoxService(log_path=os.devnull)
            if args.profile_dir:
                options.profile = webdriver.FirefoxProfile(args.profile_dir)
            return webdriver.Firefox(service=service, options=options)

        case "chrome":
            options = webdriver.ChromeOptions()
            service = ChromeService(log_path=os.devnull)
            if args.profile_dir and args.profile_name:
                options.add_argument(f"user-data-dir={args.profile_dir}")
                options.add_argument(f"--profile-directory={args.profile_name}")
            return webdriver.Chrome(service=service, options=options)

        case _:
            raise ValueError(f"Unsupported browser: {args.browser}")


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
        except (IndexError, NoSuchElementException):
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

        input(
            "Make sure to authenticate and reach the PDF preview. "
            "Once the file is loaded and the page counter is visible, press [ENTER] to start. "
            "Keep the browser in the foreground for better results.\n> [ENTER] "
        )
        sleep(2)

        total_of_pages = get_total_pages(browser)

        filename = get_output_filename(args, browser)

        logging.info(
            f'Starting the export of the file "{filename}". '
            "This might take a while depending on the number of pages."
        )

        files_list: list[str] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            # Hide the toolbar for screenshots
            try:
                hide_toolbar(browser, CLASS_NAMES_TOOLBAR)
                logging.info("Toolbar hidden for clean screenshots.")
            except NoSuchElementException:
                logging.warning(
                    "The toolbar is not visible or the CLASS_NAME_TOOLBAR is not up-to-date. "
                    "The screenshots might contain the toolbar or other errors might occur."
                )

            page_number = 1
            while page_number <= total_of_pages:
                sleep(5)
                image_path = f"{temp_dir}/{str(page_number)}.png"
                browser.find_element(By.CSS_SELECTOR, "canvas").screenshot(image_path)
                files_list.append(image_path)

                logging.info(
                    f"Page {str(page_number)} of {str(total_of_pages)} exported."
                )

                page_number += 1

                try:
                    next_page_button = find_element(
                        browser, ARIA_LABELS_NEXT_PAGE, By.XPATH
                    )
                except NoSuchElementException:
                    logging.error(
                        "Cannot find the next page button. it could be ARIA_LABEL_NEXT_PAGE is not "
                        "up-to-date or some race condition occurred. Please, try again. Saving the obtained ones."
                    )
                    break
                browser.execute_script("arguments[0].click();", next_page_button)

            logging.info(f"Saving the file as '{filename}'.")
            with open(filename, "wb") as out_file:
                out_file.write(img2pdf.convert(files_list))

            if args.keep_imgs:
                keep_dir = f"{filename}_images"
                os.makedirs(keep_dir, exist_ok=True)
                for file_path in files_list:
                    shutil.copy(file_path, keep_dir)
                logging.info(f"Images kept in directory '{keep_dir}'.")

    logging.info("Temporary images removed.")


if __name__ == "__main__":
    main()
