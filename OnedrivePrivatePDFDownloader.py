import argparse
import os
import shutil
from time import sleep

import img2pdf
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

CLASS_NAME_TOTAL_PAGES = "status_5a88b9b2"
CLASS_NAME_FILE_NAME = "OneUpNonInteractiveCommandNewDesign_156f96ef"
CLASS_NAME_TOOLBAR_HIDDEN = "root_5a88b9b2"
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
        "--profile", type=str, help="Path to the browser profile", default=None
    )
    parser.add_argument(
        "--keep-imgs",
        action="store_true",
        help="Keep the images after the PDF creation",
        default=False,
    )
    parser.add_argument("url", type=str, help="URL of the PDF file")
    return parser.parse_args()


def main() -> None:
    """Main function to export the PDF file."""
    args = parse_arguments()

    service = Service(log_path=os.devnull)
    options = webdriver.FirefoxOptions()

    if args.profile:
        options.profile = webdriver.FirefoxProfile(args.profile)

    browser = webdriver.Firefox(service=service, options=options)
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
    except ValueError:
        print(
            "The page counter is not visible or the CLASS_NAME_TOTAL_PAGES is not up-to-date. Insert the page number manually."
        )
        total_of_pages = int(input("Total of pages: "))

    page_number = 1

    try:
        filename = browser.find_element(By.CLASS_NAME, CLASS_NAME_FILE_NAME).text
    except Exception as _:
        print(
            "The file name is not visible or the CLASS_NAME_FILE_NAME is not up-to-date. Insert the file name manually."
        )
        filename = input("Please enter the file name manually: ")

    print(
        f'Starting the export of the file "{filename}". This might take a while depending on the number of pages.'
    )

    files_list: list[str] = []
    os.makedirs("tmp_images", exist_ok=True)

    # Hide the toolbar for the screenshots
    try:
        browser.execute_script(
            f"document.getElementsByClassName('{CLASS_NAME_TOOLBAR_HIDDEN}')[0].style.visibility = 'hidden' "
        )
    except NoSuchElementException:
        print(
            "The toolbar is not visible or the CLASS_NAME_TOOLBAR_HIDDEN is not up-to-date. Errors might occur."
        )

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

    print(f'Saving the file as "{filename}"')
    with open(f"{filename}", "wb") as out_file:
        out_file.write(img2pdf.convert(files_list))

    if not args.keep_imgs:
        shutil.rmtree("tmp_images")
    browser.quit()


if __name__ == "__main__":
    main()
