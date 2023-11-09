from pathlib import Path
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlite3
import logging
import time


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('backup.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Define the paths
start_dir = Path('./imgs')
backup_dir = start_dir / 'backup'
backup_info_file = Path('./backup_info.json')

# Create the "backup" folder and directory if they don't exist
backup_dir.mkdir(parents=True, exist_ok=True)

# Create the database if it doesn't exist
conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS processed_files (file_path TEXT PRIMARY KEY)')
conn.commit()

cur.close()
conn.close()

# Open the JSON file when the program starts
def is_file_processed(file_path, conn):
    cur = conn.cursor()
    cur.execute('SELECT * FROM processed_files WHERE file_path = ?', (file_path,))
    row = cur.fetchone()
    cur.close()

    if row is not None:
        logger.info(f'Already Processed: {row}')

    return row is not None


def save_db_record(file_path, conn):
    cur = conn.cursor()
    cur.execute('INSERT INTO processed_files (file_path) VALUES (?)', (str(file_path),))
    cur.close()


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

        # Open the PNG image
        with Image.open(file_path) as img:
            img = img.convert('RGB')
            new_width = img.width // 2
            new_height = img.height // 2
            img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)

            # Define the destination path with the custom folder name
            dest_path = backup_dir / custom_folder_name / relative_path.with_suffix('.jpg')
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest_path)

        #logger.info(f'Converted file: {file_path}')


class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        logger.info(f'Processed file: {event}')

        if not event.is_directory:
            file_path = Path(event.src_path)
            full_path = file_path.parent.name + file_path.name
            with sqlite3.connect('database.db') as conn:
                if file_path.is_file() and file_path.suffix.lower() == '.png' and not is_file_processed(full_path, conn):
                    time.sleep(0.35)
                    try:
                        convert_and_backup(file_path)
                        save_db_record(full_path, conn)
                    except Exception as e:
                        logger.error(f'Failed to process file: {file_path} - {e}')

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
