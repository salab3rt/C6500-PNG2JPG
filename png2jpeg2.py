import queue
import threading
import sqlite3
from pathlib import Path
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import time
from datetime import datetime

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
#backup_info_file = Path('./backup_info.json')

backup_dir.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS processed_files (file_path TEXT PRIMARY KEY)')
conn.commit()

cur.close()
conn.close()

# Create a queue to store the folders that need to be processed
process_queue = queue.Queue()

def is_folder_processed(folder_path, conn):
    cur = conn.cursor()
    cur.execute('SELECT * FROM processed_files WHERE file_path LIKE ?', (str(folder_path),))  # Use str() to ensure it's a string
    row = cur.fetchone()
    cur.close()

    if row:
        return True
    else:
        return False

# Add the existing folders to the queue
with sqlite3.connect('database.db') as conn:
    for folder in start_dir.iterdir():
        if folder.is_dir():
            if not is_folder_processed(folder, conn):
                process_queue.put(folder)

def save_db_record(full_path, conn):
        cur = conn.cursor()
        cur.execute('INSERT INTO processed_files (file_path) VALUES (?)', (str(full_path),))
        conn.commit()
        cur.close()




def process_file(file_path):
    # Convert and backup the folder
    if file_path.is_file() and file_path.suffix.lower() == '.png':
        convert_and_backup(file_path)

        full_path = file_path.parent / file_path.name  # Join directory and filename
        #print("FULLPATH from event:", full_path)

        # Mark the folder as processed
        with sqlite3.connect('database.db') as conn:
            save_db_record(full_path, conn)


    elif file_path.is_dir():
        try:
            with sqlite3.connect('database.db') as conn:
                for file in file_path.iterdir():
                    #print("FILE:",file)
                    if file.is_file() and file.suffix.lower() == '.png':
                        convert_and_backup(file)

                        full_path = file_path / file.name  # Join directory and filename
                        #print("FULLPATH from folder file:",full_path)

                        # Mark the folder as processed
                        with sqlite3.connect('database.db') as conn:
                            save_db_record(full_path, conn)
        except Exception as e:
            print(e)
            logger.error(f'Error processing {file_path}: {e}')



def worker():
    while True:
        file_path = process_queue.get()

        process_file(file_path)

        process_queue.task_done()

def convert_and_backup(file_path):
    if file_path.is_file() and file_path.suffix.lower() == '.png':
        folder_path = file_path.parent
        relative_path = folder_path.relative_to(start_dir)
        source_folder_name = folder_path.name

        custom_folder_name = source_folder_name

        if source_folder_name.startswith('u_701_'):
            custom_folder_name = 'micro_' + source_folder_name[len('u_701_'):]
        elif source_folder_name.startswith('cobas_6500_'):
            custom_folder_name = 'core_' + source_folder_name[len('cobas_6500_'):]

        try:
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                new_width = img.width // 2
                new_height = img.height // 2
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Define the destination path
                year = datetime.now().year
                dest_path = backup_dir / str(year) / custom_folder_name / file_path.name
                dest_path = dest_path.with_suffix('.jpg')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path)

                #logger.info(f'Converted file: {file_path}')

        except Exception as e:
            logger.error(f'Error processing {file_path}: {e}')

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        #logger.info(f'File created: {event.src_path}')

        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() == '.png':
                with sqlite3.connect('database.db') as conn:
                    if not is_folder_processed(file_path.name, conn):
                        process_queue.put(file_path)
                        time.sleep(0.35)

if __name__ == "__main__":
    # Start the workers
    for i in range(4):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    # Start monitoring the "imgs" folder for new files
    event_handler = FileHandler()
    observer = Observer(timeout=1.0)
    observer.schedule(event_handler, path=start_dir, recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
        observer.join()  # Wait for the observer to finish

        # Wait for the workers to finish
    process_queue.join()
