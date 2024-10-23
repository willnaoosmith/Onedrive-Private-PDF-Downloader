import argparse
import os
import shutil
from time import sleep

import img2pdf
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService

CLASS_NAME_TOTAL_PAGES = "status_5a88b9b2"
CLASS_NAME_FILE_NAME = "OneUpNonInteractiveCommandNewDesign_156f96ef"
CLASS_NAME_TOOLBAR = "root_5a88b9b2"
ARIA_LABEL_NEXT_PAGE = "Vai alla pagina successiva."


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
        help="Path to the browser profile, if supported",
        default=None,
    )
    parser.add_argument(
        "--profile-name",
        "-n",
        type=str,
        help="Profile name to use, if supported",
        default=None,
    )
    parser.add_argument(
        "--keep-imgs",
        "-k",
        action="store_true",
        help="Keep the images after the PDF creation",
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


def main() -> None:
    """Main function to export the PDF file."""
    args = parse_arguments()
    browser = get_browser(args)
    browser.get(args.url)

    input(
        "Make sure to authenticate and reach the PDF preview. Once the file is loaded and the page counter is visible, press [ENTER] to start."
    )
    sleep(2)

    try:
        total_of_pages = int(
            browser.find_element(By.CLASS_NAME, CLASS_NAME_TOTAL_PAGES).text.replace(
                "/", ""
            )
        )
    except ValueError | NoSuchElementException:
        print(
            "The page counter is not visible or the CLASS_NAME_TOTAL_PAGES is not up-to-date."
            "Insert the page number manually."
        )
        total_of_pages = int(input("Total of pages: "))

    try:
        filename = browser.find_element(By.CLASS_NAME, CLASS_NAME_FILE_NAME).text
    except NoSuchElementException:
        print(
            "The file name is not visible or the CLASS_NAME_FILE_NAME is not up-to-date. Insert the file name manually."
        )
        filename = input("Please enter the file name manually: ")

    print(
        f'Starting the export of the file "{filename}". This might take a while depending on the number of pages.'
    )

    files_list: list[str] = []
    os.makedirs("tmp_images", exist_ok=True)

    # Hide the toolbar for screenshots
    try:
        browser.execute_script(
            f"document.getElementsByClassName('{CLASS_NAME_TOOLBAR}')[0].style.visibility = 'hidden'"
        )
    except NoSuchElementException:
        print(
            "The toolbar is not visible or the CLASS_NAME_TOOLBAR_HIDDEN is not up-to-date. Errors might occur."
        )

    page_number = 1
    while page_number <= total_of_pages:
        sleep(5)
        browser.find_element(By.CSS_SELECTOR, "canvas").screenshot(
            f"tmp_images/{str(page_number)}.png"
        )
        files_list.append(f"tmp_images/{str(page_number)}.png")

        print(f"Page {str(page_number)} of {str(total_of_pages)} exported.")

        page_number += 1

        try:
            next_page_button = browser.find_elements(
                By.XPATH, f"//button[@aria-label='{ARIA_LABEL_NEXT_PAGE}']"
            )[-1]
        except NoSuchElementException:
            print(
                "Cannot find the next page button, it could be ARIA_LABEL_NEXT_PAGE"
                "is not up-to-date or some race condition occurred. Please, try again."
            )
            break
        browser.execute_script("arguments[0].click();", next_page_button)

    print(f'Saving the file as "{filename}".')
    with open(f"{filename}", "wb") as out_file:
        out_file.write(img2pdf.convert(files_list))

    if not args.keep_imgs:
        shutil.rmtree("tmp_images")
    browser.quit()


if __name__ == "__main__":
    main()
