import queue
import threading
import sqlite3
from pathlib import Path
import os
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import time
from datetime import datetime
from tqdm import tqdm, trange
from colorama import just_fix_windows_console
just_fix_windows_console()


def setup_logging():
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    
    file_handler = logging.FileHandler('backup.log')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Define the paths
start_dir = Path('./imgs')
backup_dir = start_dir / 'backup'

backup_dir.mkdir(parents=True, exist_ok=True)

#main_conn = sqlite3.connect('database.db', check_same_thread=False)
#cur = main_conn.cursor()
#
#cur.execute('CREATE TABLE IF NOT EXISTS processed_files (file_path TEXT PRIMARY KEY)')
#main_conn.commit()
#cur.close()

# Create a queue to store the folders that need to be processed
process_queue = queue.Queue()

#def is_folder_processed(folder_path, file_count = 0):
#    try:
#        with main_conn:
#            cur = main_conn.cursor()
#            cur.execute('SELECT * FROM processed_files WHERE file_path LIKE ?', (str(folder_path) + '%',))
#            row = cur.fetchall()
#            cur.close()
#            if row and len(row) >= file_count:
#                return True
#            else:
#                return False
#    except Exception as e:
#        logger.error(f'SQLite Error: {e}')
        
def is_processed(file_path):
    #print(file_path)
    parent_folder = file_path.parent.name
    custom_folder_name = ''
    #print(parent_folder)
    if parent_folder.startswith('u_701_'):
        custom_folder_name = 'micro_' + parent_folder[len('u_701_'):]
        
    elif parent_folder.startswith('cobas_6500_'):
        custom_folder_name = 'core_' + parent_folder[len('cobas_6500_'):]
        
    #print(custom_folder_name)
        
    year = datetime.now().year
    dest_path = backup_dir / str(year) / custom_folder_name / file_path.name
    dest_path = dest_path.with_suffix('.jpg')
    #print('Dest:' + str(dest_path))
    
    if dest_path.is_file():
        #print('True')
        return True
    else:
        #print('False')
        return False
        

def get_file_count_in_folder(folder_path):
    return sum(1 for _ in folder_path.glob('*.png'))

# Add the existing folders to the queue
#with main_conn:
    for folder in start_dir.iterdir():
        if folder.is_dir():
            file_count = get_file_count_in_folder(folder)
            if not is_folder_processed(folder, file_count=file_count):
                process_queue.put(folder)

#def save_db_record(records, conn):
#    try:
#        cur = conn.cursor()
#        cur.execute('INSERT INTO processed_files (file_path) VALUES (?)', (str(records),))
#        conn.commit()
#        cur.close()
#    except Exception as e:
#        logger.error(f'SQLite Error: {e}')
        



def process_file(file_path):
    try:
        if not is_processed(file_path):
            print('Processing files..')
            #with tqdm(desc="Processing file", unit="files", leave=True) as progress_bar:
            #with sqlite3.connect('database.db') as conn:
            if file_path.is_file() and file_path.suffix.lower() == '.png':
                with tqdm(total=len(range(1)), desc=f'{file_path.name[:20]}', unit='file', leave=True) as pbar:
                    convert_and_backup(file_path)
                    #full_path = file_path.parent / file_path.name  # Join directory and filename
                    #save_db_record(full_path, conn)
                    pbar.update(1)
                    #pbar.delay(1.0)

                    #progress_bar.update()
                    #progress_bar.refresh()
                #pbar.clear()
                #pbar.close()
                # if process_queue.qsize() == 0:
                #     os.system('cls')
                #     print('Waiting for new files..')

            elif file_path.is_dir():
                with tqdm(total=get_file_count_in_folder(file_path), desc=f'{file_path.name[:21]}', unit='file') as pbar:
                    for file in file_path.iterdir():
                        if file.is_file() and file.suffix.lower() == '.png':
                            convert_and_backup(file)
                            #full_path = file_path / file.name
                            #save_db_record(full_path, conn)
                        pbar.update(1)

                pbar.clear()
                pbar.close()
                os.system('cls')
                                
    except Exception as e:
        print(e)
        logger.error(f'Error processing {file_path}: {e}')
    #finally:
        
        #print('Waiting for new files..')
    



def worker():
    try:
        while True:
            
            file_path = process_queue.get()
            process_file(file_path)
            process_queue.task_done()
                
            
    except Exception as e:
        print(e)
        logger.error(f'Worker thread error: {e}')
        

# Function to convert and backup a file
def convert_and_backup(file_path):
    #print(file_path)
    if file_path.is_file() and file_path.suffix.lower() == '.png':  # Check if it's a file
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

                year = datetime.now().year
                dest_path = backup_dir / str(year) / custom_folder_name / file_path.name
                dest_path = dest_path.with_suffix('.jpg')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path)

                #logger.info(f'Converted file: {file_path}')

        except Exception as e:
            logger.error(f'Error processing {file_path}: {e}')

def wait_for_readable(file_path, max_wait_seconds=5, sleep_duration=0.2):
    """
    Wait for the file to become readable or until the maximum wait time is reached.

    Parameters:
    - file_path: Path to the file.
    - max_wait_seconds: Maximum time to wait for the file to become readable.
    - sleep_duration: Time to sleep between checks.

    Returns:
    - True if the file becomes readable, False otherwise.
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        if os.access(file_path, os.R_OK):
            return True

        time.sleep(sleep_duration)

    return False


processed_files = set()  # Set to track processed file paths

class FileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.added_to_queue = set()
        self.reset_threshold = 100  # Adjust the threshold

    def on_created(self, event):
        try:
            if not event.is_directory:
                file_path = Path(event.src_path)
                if file_path.suffix.lower() == '.png':
                    # Check if the file has already been added to the queue
                    if file_path not in self.added_to_queue:
                        #file_count = get_file_count_in_folder(file_path.parent)
                        if not is_processed(file_path.parent):
                            if wait_for_readable(file_path):
                                process_queue.put(file_path)
                                self.added_to_queue.add(file_path)

                            # Reset the set if it reaches the threshold
                if len(self.added_to_queue) >= self.reset_threshold:
                    self.added_to_queue = set()
        except Exception as e:
            logger.error(f'Event Error: {e}, Event: {event}')

if __name__ == "__main__":
    #Setup logger
    logger = setup_logging()
    

    workers = []
    for i in range(4):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        workers.append(t)

    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=start_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('Terminating Script, waiting Job to finish')
        observer.stop()
        observer.join()  # Wait for the observer to finish

        process_queue.join()
        #main_conn.close()
        os.system('cls')
    finally:
        print('Script Terminated.. ')
    