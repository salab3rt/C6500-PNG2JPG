import json
from pathlib import Path
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the paths
start_dir = Path('./imgs')
backup_dir = start_dir / 'backup'
backup_info_file = Path('./backup_info.json')
log_file = Path('./processed_files.json')  # New log file for tracking processed files

# Create the "backup" folder and directory if they don't exist
backup_dir.mkdir(parents=True, exist_ok=True)

# Initialize a dictionary to store the backed-up folder names and file names
backed_up_data = {}

# Function to convert and backup a file
def convert_and_backup(file_path):
    if file_path.suffix.lower() == '.png':
        folder_path = file_path.parent
        relative_path = file_path.relative_to(folder_path)
        source_folder_name = folder_path.name

        custom_folder_name = source_folder_name  # Initialize it with the original folder name

        if source_folder_name.startswith('u_701_'):
            custom_folder_name = 'micro_' + source_folder_name[len('u_701_'):]
        elif source_folder_name.startswith('cobas_6500_'):
            custom_folder_name = 'core_' + source_folder_name[len('cobas_6500_'):]

        # Check if the file has been processed for this folder
        if not is_file_processed(log_file, custom_folder_name, relative_path):
            # Open the PNG image
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                new_width = img.width // 2
                new_height = img.height // 2
                img = img.resize((new_width, new_height))

                # Define the destination path with the custom folder name
                dest_path = backup_dir / custom_folder_name / relative_path.with_suffix('.jpg')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path)

            # Log the processed file
            log_processed_file(log_file, source_folder_name, relative_path)

# Function to check if a file has been processed
def is_file_processed(log_file, folder_name, relative_path):
    processed_files = load_processed_files(log_file)
    return folder_name in processed_files and relative_path in processed_files[folder_name]

# Function to log a processed file
def log_processed_file(log_file, folder_name, relative_path):
    processed_files = load_processed_files(log_file)
    if folder_name in processed_files:
        processed_files[folder_name].append(relative_path)
    else:
        processed_files[folder_name] = [relative_path]
    save_processed_files(log_file, processed_files)

# Function to load the processed files data
def load_processed_files(log_file):
    if not log_file.exists():
        return {}

    with open(log_file, 'r') as file:
        return json.load(file)

# Function to save the processed files data
def save_processed_files(log_file, data):
    with open(log_file, 'w') as file:
        json.dump(data, file, default=str)

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.is_file() and file_path.suffix.lower() == '.png':
                convert_and_backup(file_path)

if __name__ == "__main__":
    # Start monitoring the "imgs" folder for new files
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=start_dir, recursive=True)
    observer.start()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
