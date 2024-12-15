# PDF Exporter from Authenticated OneDrive Sessions

This project allows you to export PDFs, even those that are protected, from authenticated OneDrive sessions using Selenium. The tool automates the browser process to capture screenshots of each page and combine them into a PDF file. Works also on OneDrive for Business.

> [!WARNING]
> This tool may need to be calibrated in order to work correctly. It is expected to be used by someone who can inspect a page and read HTML.


- [PDF Exporter from Authenticated OneDrive Sessions](#pdf-exporter-from-authenticated-onedrive-sessions)
  - [Features](#features)
  - [Preview](#preview)
  - [Requirements](#requirements)
    - [Python Packages:](#python-packages)
    - [Browsers:](#browsers)
    - [Browser Drivers:](#browser-drivers)
  - [Installation and Setup](#installation-and-setup)
  - [Usage](#usage)
    - [Command-line Options](#command-line-options)
    - [Example Command:](#example-command)
    - [Profile Setup:](#profile-setup)
  - [Calibrating the Tool](#calibrating-the-tool)
    - [Steps to Calibrate:](#steps-to-calibrate)
  - [Contributing](#contributing)


## Features
- Supports both Firefox and Chrome browsers.
- Ability to export protected PDFs from authenticated web sessions.
- Can optionally keep or delete temporary images used for PDF creation.
- Compatible with browser profiles to retain session data (useful for skipping the login).


## Preview

```bash
$ python OnedrivePrivatePDFDownloader.py --profile-dir /path/to/profile https://blabla.sharepoint.com/...

INFO - Initializing browser: firefox
Make sure to authenticate and reach the PDF preview. 
INFO - Total number of pages detected: 8
INFO - Detected file name: '2024-10-21.pdf'
INFO - Starting the export of the file "2024-10-21.pdf". This might take a while depending on the number of pages.
INFO - Toolbar hidden for clean screenshots.
INFO - Page 1 of 8 exported.
INFO - Page 2 of 8 exported.
INFO - Page 3 of 8 exported.
INFO - Page 4 of 8 exported.
INFO - Page 5 of 8 exported.
INFO - Page 6 of 8 exported.
INFO - Page 7 of 8 exported.
INFO - Page 8 of 8 exported.
INFO - Saving the file as '2024-10-21.pdf'.
INFO - Temporary images removed.
INFO - Browser session ended.
```


## Requirements

Before running the project, you need the following dependencies:

### Python Packages:
Install the required Python packages using the following command:

```bash
pip install -r requirements.txt
```

### Browsers:
Make sure that you have one of the following browsers installed:
- Firefox
- Chrome

### Browser Drivers:
To interact with your browser via Selenium, you need the appropriate driver for your browser:
- **Geckodriver** for Firefox: [Download Geckodriver](https://github.com/mozilla/geckodriver/releases/latest)
- **Chromedriver** for Chrome: [Download Chromedriver](https://googlechromelabs.github.io/chrome-for-testing/#stable)

Ensure the drivers are in your system’s `PATH` or specify their location explicitly when launching the browser.

## Installation and Setup

1. Clone this repository:
    ```bash
    git clone https://github.com/willnaoosmith/Onedrive-Private-PDF-Downloader
    cd Onedrive-Private-PDF-Downloader
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Download and install the appropriate browser drivers for your browser.

4. Optionally, set up a browser profile to retain session information:
    - **Firefox:**
        - Create a Firefox profile through `about:profiles` in the browser's address bar.
        - Use the `-p` option to specify the path to the Firefox profile directory.
    - **Chrome:**
        - Specify the Chrome user data directory and profile name using `-p` and `-n` options. You can find this in `chrome://version/`.

## Usage

To run the script, use the following command structure:

```bash
python OnedrivePrivatePDFDownloader.py [options] <url>
```

### Command-line Options

| Argument             | Description                                                                              | Example                             |
| -------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------- |
| `--browser, -b`      | Specify the browser to use (`firefox` or `chrome`).                                      | `--browser firefox`                 |
| `--profile-dir, -p`  | Path to the browser profile directory. If using Chrome, specify the user data directory. | `--profile-dir /path/to/profile`    |
| `--profile-name, -n` | Profile name to use (Chrome only).                                                       | `--profile-name "Profile 1"`        |
| `--keep-imgs, -k`    | Keep the temporary images used for PDF creation.                                         | `--keep-imgs`                       |
| `--output-file, -o`  | Specify the output file name.                                                            | `--output-file file.pdf`            |
| `url`                | The URL of the PDF file. This is a required argument.                                    | `https://blabla.sharepoint.com/...` |

### Example Command:

```bash
python OnedrivePrivatePDFDownloader.py --profile-dir /path/to/profile https://blabla.sharepoint.com/...
```

This command will open Firefox using the specified profile and navigate to the given URL. The script will then export the PDF file and save it in the current directory.


### Profile Setup:
To use an authenticated session, you may need to use a browser profile where you're already logged in. Here’s how to do that:

- **Firefox Profile:**
    1. Open Firefox and type `about:profiles` in the address bar.
    2. Create a new profile or use an existing one. The profile path will be displayed under "Root Directory."
    3. Use the `--profile-dir` option to point to this directory in the script.

- **Chrome Profile:**
    1. Open Chrome and type `chrome://version` in the address bar.
    2. Find the `Profile Path`
    3. Use the `--profile-dir` option for the user data directory (e.g., `/path/to/profiles`) and the `--profile-name` option for the profile name (e.g., `Default`).

## Calibrating the Tool

If the tool is not working correctly, you may need to update the class names and ARIA labels used to identify elements on the OneDrive page. These values are defined in the [OnedrivePrivatePDFDownloader.py](/OnedrivePrivatePDFDownloader.py#L18) file.

### Steps to Calibrate:

1. **Open the OneDrive page in your browser:**
   - Use the browser's inspector tool to find the class names and ARIA labels for the elements used by the script.

2. **Update the class names and ARIA labels in the script:**
   - Open the [OnedrivePrivatePDFDownloader.py](/OnedrivePrivatePDFDownloader.py#L18) file.
   - Update the following lists with the new values:
     ```python
     CLASS_NAMES_TOTAL_PAGES = ["status_5a88b9b2"]  # Add the new class names for the total pages element
     CLASS_NAMES_FILE_NAME = ["OneUpNonInteractiveCommandNewDesign_156f96ef"]  # Add the new class names for the file name element
     CLASS_NAMES_TOOLBAR = ["root_5a88b9b2"]  # Add the new class names for the toolbar element
     ARIA_LABELS_NEXT_PAGE = ["Vai alla pagina successiva."]  # Add the new ARIA labels for the next page button
     ```

3. **Save the changes and run the script again:**
   - Save the updated [OnedrivePrivatePDFDownloader.py](/OnedrivePrivatePDFDownloader.py) file.
   - Run the script with the updated values to ensure it works correctly.

By following these steps, you can calibrate the tool to work with any changes in the OneDrive page structure.


## Contributing

We welcome contributions to improve this tool. If you have found new class names or ARIA labels, please consider submitting a pull request to update the configuration.

For more details, see the [CONTRIBUTING.md](/CONTRIBUTING.md) file.
