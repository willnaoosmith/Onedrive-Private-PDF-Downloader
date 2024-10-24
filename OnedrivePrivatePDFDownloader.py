import argparse
import logging
import os
import shutil
from time import sleep, time

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
        description="Export a PDF (also the protected ones) from an authenticated session."
    )
    parser.add_argument(
        "--browser",
        "-b",
        type=str,
        choices=["firefox", "chrome"],
        help="Browser to use (firefox or chrome)",
        default="firefox",
    )
    parser.add_argument(
        "--profile-dir",
        "-p",
        type=str,
        help="Path to the browser profile.",
        default=None,
    )
    parser.add_argument(
        "--profile-name",
        "-n",
        type=str,
        help="Profile name to use, only for Chrome.",
        default=None,
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
    parser.add_argument("url", type=str, help="URL of the PDF file")
    return parser.parse_args()


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

    logging.info(f"Initializing browser: {args.browser}")

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
            logging.error(f"Unsupported browser: {args.browser}")
            raise ValueError(f"Unsupported browser: {args.browser}")


def find_element_by_class_names(browser, class_names):
    """Find an element by one of the class names in the list.

    Args:
        browser (webdriver): Browser instance
        class_names (list[str]): List of class names to search

    Raises:
        NoSuchElementException: If no element is found

    Returns:
        WebElement: The found element
    """
    for class_name in class_names:
        try:
            element = browser.find_element(By.CLASS_NAME, class_name)
            logging.debug(f"Element found using class name: '{class_name}'")
            return element
        except NoSuchElementException:
            logging.debug(f"Element not found using class name: '{class_name}'")
            continue
    raise NoSuchElementException(
        f"No element found with any of the class names: '{class_names}'"
    )


def find_next_page_button(browser, aria_labels):
    """Find the next page button by one of the aria labels in the list.

    Args:
        browser (WebDriver): Browser instance
        aria_labels (list[str]): List of aria labels to search

    Raises:
        NoSuchElementException: If no element is found

    Returns:
        WebElement: The found element
    """
    for aria_label in aria_labels:
        try:
            next_page_button = browser.find_elements(
                By.XPATH, f"//button[@aria-label='{aria_label}']"
            )[-1]
            logging.debug(f"Next page button found using aria label: '{aria_label}'")
            return next_page_button
        except NoSuchElementException:
            logging.debug(
                f"Next page button not found using aria label: '{aria_label}'"
            )
            continue
    raise NoSuchElementException(
        f"No next page button found with any of the aria labels: '{aria_labels}'"
    )


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
        f"No toolbar found with any of the class names: '{class_names}'"
    )


def main() -> None:
    """Main function to export the PDF file."""
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    browser = get_browser(args)
    browser.get(args.url)

    input(
        "Make sure to authenticate and reach the PDF preview. "
        "Once the file is loaded and the page counter is visible, press [ENTER] to start. "
        "Keep the browser in the foreground for better results."
    )
    sleep(2)

    try:
        total_of_pages = int(
            find_element_by_class_names(browser, CLASS_NAMES_TOTAL_PAGES).text.replace(
                "/", ""
            )
        )
        logging.info(f"Total number of pages detected: {total_of_pages}")
    except (ValueError, NoSuchElementException):
        logging.warning(
            "The page counter is not visible or the CLASS_NAME_TOTAL_PAGES is not up-to-date."
        )
        total_of_pages = int(input("Insert the total number of pages manually: "))

    try:
        filename = find_element_by_class_names(browser, CLASS_NAMES_FILE_NAME).text
        logging.info(f"Detected file name: {filename}")
    except NoSuchElementException:
        logging.warning(
            "The file name is not visible or the CLASS_NAME_FILE_NAME is not up-to-date."
        )
        filename = input(
            "Insert the file name manually (with the extension e.g.: file.pdf): "
        )

    logging.info(
        f'Starting the export of the file "{filename}". '
        "This might take a while depending on the number of pages."
    )

    files_list: list[str] = []
    temp_dir = f"tmp/tmp_images_{int(time())}"
    os.makedirs(temp_dir, exist_ok=True)

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
        browser.find_element(By.CSS_SELECTOR, "canvas").screenshot(
            f"{temp_dir}/{str(page_number)}.png"
        )
        files_list.append(f"{temp_dir}/{str(page_number)}.png")

        logging.info(f"Page {str(page_number)} of {str(total_of_pages)} exported.")

        page_number += 1

        try:
            next_page_button = find_next_page_button(browser, ARIA_LABELS_NEXT_PAGE)
        except NoSuchElementException:
            logging.error(
                "Cannot find the next page button. it could be ARIA_LABEL_NEXT_PAGE is not "
                "up-to-date or some race condition occurred. Please, try again. Saving the obtained ones."
            )
            break
        browser.execute_script("arguments[0].click();", next_page_button)

    logging.info(f'Saving the file as "{filename}".')
    with open(f"{filename}", "wb") as out_file:
        out_file.write(img2pdf.convert(files_list))

    if not args.keep_imgs:
        shutil.rmtree("tmp", ignore_errors=True)
        logging.info("Temporary images removed.")

    browser.quit()
    logging.info("Browser session ended.")


if __name__ == "__main__":
    main()
