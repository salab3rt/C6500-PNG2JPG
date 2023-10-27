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

def load_backed_up_data():
    if not backup_info_file.exists():
        # Create the file if it doesn't exist
        with open(backup_info_file, 'w') as json_file:
            json.dump({}, json_file)

    with open(backup_info_file, 'r') as json_file:
        return json.load(json_file)

# Initialize a dictionary to store the backed-up folder names and file names
backed_up_data = load_backed_up_data()

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

        print('relative', relative_path)
        print('folder', folder_path)
        print('source folder', source_folder_name)
        
        if relative_path not in backed_up_data.get(source_folder_name, []):
            # Open the PNG image
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                new_width = img.width // 2
                new_height = img.height // 2
                img = img.resize((new_width, new_height), Image.LANCZOS)

                # Define the destination path with the custom folder name
                dest_path = backup_dir / custom_folder_name / relative_path.with_suffix('.jpg')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path)

            # Update the backed-up data
            if source_folder_name in backed_up_data:
                backed_up_data[source_folder_name].append(relative_path.name)
            else:
                backed_up_data[source_folder_name] = [relative_path.name]
            save_backed_up_data(backed_up_data)



def load_backed_up_data():
    if not backup_info_file.exists():
        # Create the file if it doesn't exist
        with open(backup_info_file, 'w') as json_file:
            json.dump({}, json_file)

    with open(backup_info_file, 'r') as json_file:
        return json.load(json_file)

def save_backed_up_data(data):
    with open(backup_info_file, 'w') as json_file:
        json.dump(data, json_file)

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
