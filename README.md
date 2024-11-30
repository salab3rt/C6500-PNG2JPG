# C6500-PNG2JPG - WIP

### Purpose

This script addresses a real-world problem where urine sediment microscope images need to be stored for over a year. Each image is typically ~1MB in size, but the laboratory infrastructure automatically deletes them after 5 days. The script reduces disk usage by downscaling and converting these images to JPG format, shrinking each file to only ~50KB while maintaining excellent quality. This allows for long-term storage without space constraints.


This script monitors a specified folder for new `.png` files. When a new file is detected, it performs the following actions:
- Downscales the image to half its original size.
- Converts the image to `.jpg`.
- Saves the processed image to a specified output folder, preserving an organized structure.

## Features

- **Folder Monitoring**: Uses OS notifications to detect file changes in a watch directory.
- **Image Processing**:
  - Converts `.png` files to `.jpg`.
  - Resizes images using high-quality downscaling.
- **Organized Backup**: Saves processed images in an output folder, structured by year and custom naming conventions.
- **Multithreading**: Efficiently processes files and folders in parallel.
- **Logging**: Logs are stored in backup.log and include details about processed files and errors.

## Requirements

- Python 3.8 or later
- Windows OS
- Required Python libraries:
  - `Pillow` (Image processing)
  - `pywin32` (File monitoring)
  - `colorama` (Console text styling)
  - `tqdm` (Progress bars)
  - `logging` (Logging functionality)

## Installation

1. Clone this repository or download the script.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

---

## Ensure Directories Are Correctly Defined

- Update the `start_dir` variable in the script with the folder to monitor (e.g., `'X:'`).
- Update the `backup_dir` variable with the desired output directory (default: `start_dir/backup`).

---

## Usage

1. Define the directories as described above.
2. Run the script:
   ```bash
   python png2jpg.py

## Shortcuts
- Terminate the script safely: `Ctrl + C`.

## Output Structure

Processed files are saved in the following structure:

![image](https://github.com/user-attachments/assets/b4bd3b9b-af23-4acd-bbfa-c93fea757a13)

---

## Contributing
- Contributions are welcome! Feel free to submit issues or pull requests.

## License
- This project is licensed under the MIT License.

## Acknowledgments
- Pillow for image processing.
- pywin32 for directory monitoring.
- tqdm for progress bars.
- colorama for console output styling.

