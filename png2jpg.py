import os
import time
import json
from pathlib import Path
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the paths
start_dir = Path('./imgs')
backup_dir = start_dir / 'backup'
backup_info_file = Path('./backup_info.json')


# Create the "backup" folder and directory if they don't exist
backup_dir.mkdir(parents=True, exist_ok=True)

# Initialize a dictionary to store the backed-up folder names and file names
backed_up_data = {}

# Function to convert and backup a folder
def convert_and_backup(folder_path):
    for item in folder_path.glob('*'):
        if item.is_file() and item.suffix.lower() == '.png':

            # Open the PNG image
            with Image.open(item) as img:
                # Convert the image to RGB mode to remove the alpha channel
                img = img.convert('RGB')
                new_width = img.width // 2
                new_height = img.height // 2
                # Resize the image to the desired dimensions
                img = img.resize((new_width, new_height), Image.ANTIALIAS)

                # Get the relative path to the original image
                relative_path = item.relative_to(folder_path)

                # Create the destination path in the "backup" subdirectory
                dest_folder_name = folder_path.name

                if dest_folder_name.startswith('u_701_'):
                    dest_folder_name = 'micro_' + dest_folder_name[len('u_701_'):]
                elif dest_folder_name.startswith('cobas_6500_'):
                    dest_folder_name = 'core_' + dest_folder_name[len('cobas_6500_'):]

                dest_path = backup_dir / dest_folder_name / relative_path.with_suffix('.jpg')

                # Ensure that the parent directories exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Save the scaled image as a JPG in the "backup" subdirectory
                img.save(dest_path)
                print('Saved as:', dest_path)

            # Update the backed-up data
            if folder_path.name in backed_up_data:
                backed_up_data[folder_path.name].append(relative_path.name)
            else:
                backed_up_data[folder_path.name] = [relative_path.name]

            # Save the updated data to the JSON file
            save_backed_up_data(backed_up_data)

def load_backed_up_data():
    if backup_info_file.exists():
        with open(backup_info_file, 'r') as json_file:
            return json.load(json_file)
    return {}

def save_backed_up_data(data):
    with open(backup_info_file, 'w') as json_file:
        json.dump(data, json_file)

class FileHandler(FileSystemEventHandler):
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def on_created(self, event):
        if event.is_file and event.src_path.endswith('.png'):
            print(f'New file detected in {self.folder_path}: {event.src_path}')
            convert_and_backup(self.folder_path)

class DirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            folder_path = Path(event.src_path)
            folder_name = folder_path.name
            if folder_name not in backed_up_data:
                print(f'New folder detected: {folder_name}')

                # Wait for the copying process to complete (e.g., 10 seconds)
                time.sleep(5)

                convert_and_backup(folder_path)


def monitor_changes():
    try:
        while True:
            # Check for changes in the original folders every 60 seconds
            for folder_name in backed_up_data.keys():
                folder_path = start_dir / folder_name
                for item in folder_path.glob('*'):
                    print(item)
                    if item.is_file() and item.suffix.lower() == '.png':
                        if item.relative_to(folder_path) not in backed_up_data[folder_name]:
                            print(f'New file detected in {folder_name}: {item.name}')
                            convert_and_backup(folder_path)
                    break
            time.sleep(60)

    except KeyboardInterrupt:
        print("Quitting Program")

if __name__ == "__main__":
    backed_up_data = load_backed_up_data()

    # Start monitoring the "img" folder for new folders
    event_handler = DirectoryHandler()
    observer = Observer()
    observer.schedule(event_handler, path=start_dir, recursive=False)
    observer.start()
    monitor_changes()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
