# Contributing to Onedrive-Private-PDF-Downloader

We welcome contributions to improve this tool. If you have found new class names or ARIA labels that work on your end, please consider submitting a pull request to update the configuration, so others can benefit from it as well.

## How to Contribute

1. **Fork the repository:**
   - Click the "Fork" button at the top right of this repository page.

2. **Clone your forked repository:** 
   - Replace `<your-username>` with your GitHub username.
   ```bash
   git clone https://github.com/<your-username>/Onedrive-Private-PDF-Downloader.git
   cd Onedrive-Private-PDF-Downloader
   ```

1. **Create a new branch:**
   ```bash
   git checkout -b update-config
   ```

2. **Make your changes:**
   - Update the class names and/or ARIA labels in the [OnedrivePrivatePDFDownloader.py](/OnedrivePrivatePDFDownloader.py#L18) file. See the [Calibrating the Tool](/README.md#calibrating-the-tool) section for more details.

3. **Commit your changes:**
   - Replace `<commit-message>` with a short description of your changes.
   ```bash
   git add OnedrivePrivatePDFDownloader.py
   git commit -m "feat: <commit-message>"
   ```

4. **Push your changes to your forked repository:**
   ```bash
   git push origin update-config
   ```

5. **Create a pull request:**
   - Go to the original repository and click the "New pull request" button.
   - Select your branch and submit the pull request.

Thank you for contributing!