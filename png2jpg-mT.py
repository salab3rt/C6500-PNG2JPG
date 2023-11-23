import queue
import threading
from pathlib import Path
from os import system, access, R_OK
from PIL import Image
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import logging
import time
from datetime import datetime
from tqdm import tqdm
from colorama import just_fix_windows_console



def setup_logging():
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    
    file_handler = logging.FileHandler('backup.log')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def full_folder_backup(start_folder):
    for folder in start_folder.iterdir():
        if folder.is_dir():
            with files_lock:
                try:
                    files_to_process.add(folder)
                except Exception as e:
                    logger.error(f'Error reading {folder}: {e}')
                finally:
                    pass


def is_readable(file_path, max_wait_seconds=5, sleep_duration=0.2):
    try:
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            if access(file_path, R_OK):
                return True

            time.sleep(sleep_duration)
        logger.error(f'Error reading {file_path}')
        return False
    except Exception as e:
            logger.error(f'Error reading {file_path}: {e}')


def is_processed(file_path):
    
    parent_folder = file_path.parent.name
    custom_folder_name = ''
    if parent_folder.startswith('u_701_'):
        custom_folder_name = 'micro_' + parent_folder[len('u_701_'):]

    elif parent_folder.startswith('cobas_6500_'):
        custom_folder_name = 'core_' + parent_folder[len('cobas_6500_'):]

    year = datetime.now().year
    dest_path = backup_dir / str(year) / custom_folder_name / file_path.name
    dest_path = dest_path.with_suffix('.jpg')

    if dest_path.is_file():
        return True
    else:
        return False
        

def get_file_count_in_folder(folder_path):
    return sum(1 for _ in folder_path.glob('*.png'))


def process_file(path):
    try:
        if is_readable(path):
            if path.is_dir():
                with tqdm(total=get_file_count_in_folder(path), desc=f'{path.name[:23]}', unit='file', bar_format="{desc} |{bar}| [{n_fmt}/{total_fmt}] {elapsed} - {rate_fmt}{postfix}") as pbar:
                    for file in path.iterdir():
                        if file.suffix.lower() == '.png' and not is_processed(file):
                            convert_and_backup(file)
                        pbar.update(1)
                #system('cls')
                return True

            elif path.suffix.lower() == '.png' and not is_processed(path):
                    with tqdm(total=1, desc=f'{path.name[:23]}', unit='file', leave=True, position=0, bar_format="{desc} |{bar}| {rate_fmt}") as pbar:
                        converted_file = convert_and_backup(path)
                        pbar.update(1)
                    return converted_file
        else:
            logger.error(f'Error processing {path}')
            return None
                                
    except Exception as e:
        print(e)
        logger.error(f'Error processing {path}: {e}')
        
    #finally:
    #    if not files_to_process:
    #        system('cls')
            
            
class FileHandler(FileSystemEventHandler):

    def on_created(self, event):
        try:
            if event.is_directory:
                folder_path = Path(event.src_path)
                folders_lock.acquire(blocking=True, timeout=2)
                folder_process_queue.put(folder_path)
                folders_lock.release
        except Exception as e:
            logger.error(f'On created Event Error: {e}, Event: {event}')
    
    def on_modified(self, event):
        try:
            if event.is_directory:
                folder_path = Path(event.src_path)
                if access(folder_path, R_OK) and folder_path.is_dir() and event.src_path != start_dir.name:
                    #print(event)
                    folders_lock.acquire(blocking=True, timeout=2)
                    folder_process_queue.put(folder_path)
                    folders_lock.release

        except Exception as e:
            print(e)
            logger.error(f'On modified Event Error: {e}')

def folder_worker():
    try:
        while True:
            time.sleep(.001)
            folders_lock.acquire(blocking=True, timeout=2)
            folder_path = folder_process_queue.get()
            folders_lock.release
            
            folder = Path(folder_path)
            for file in folder.iterdir():
                if file.suffix.lower() == '.png':
                    with files_lock:
                        files_to_process.add(file)
            folder_process_queue.task_done()
            
    except Exception as e:
        print(e)
        logger.error(f'Folder thread error: {e}')


def file_worker():
    max_retries = 3

    while True:
        try:
            time.sleep(.01)
            if len(files_to_process) > 0:
                with files_lock:
                    file_path = files_to_process.pop()
                if file_path and not is_processed(file_path):
                    retries = 0
                    while retries < max_retries:
                        processed_file = process_file(file_path)
                        if not processed_file:
                            retries += 1
                            logger.warning(f"Processing failed for {file_path}. Retrying attempt {retries}/{max_retries}")
                        else:
                            break  # Break out of the retry loop on successful processing
                    if retries == max_retries:
                        logger.error(f"Max retries reached for {file_path}. Skipping file.")
                    
        except Exception as e:
            print(e)
            logger.error(f'File thread error: {e}')
        

# Function to convert and backup a file
def convert_and_backup(file_path):
    try:
        folder_path = file_path.parent
        source_folder_name = folder_path.name
        custom_folder_name = source_folder_name

        if source_folder_name.startswith('u_701_'):
            custom_folder_name = 'micro_' + source_folder_name[len('u_701_'):]
        if source_folder_name.startswith('cobas_6500_'):
            custom_folder_name = 'core_' + source_folder_name[len('cobas_6500_'):]

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
    
        return dest_path
            #logger.info(f'Converted file: {file_path}')

    except Exception as e:
        logger.error(f'Error processing {file_path}: {e}')


if __name__ == "__main__":
    
    just_fix_windows_console()
    
    
    # Define the paths
    #start_dir = Path('X:')
    start_dir = Path('./imgs')

    backup_dir = start_dir / 'backup'

    backup_dir.mkdir(parents=True, exist_ok=True)

    folder_process_queue = queue.Queue(maxsize=-1)

    files_to_process = set()
    files_lock = threading.Lock()
    folders_lock = threading.Lock()
    
    #Setup logger
    logger = setup_logging()
    
    event_handler = FileHandler()
    observer = PollingObserver()
    observer.schedule(event_handler, path=start_dir, recursive=False)
    observer.start()
    
    folder_workers = []
    for i in range(3):
        t = threading.Thread(target=folder_worker)
        t.daemon = True
        t.start()
        folder_workers.append(t)

    files_workers = []
    for i in range(9):
        t = threading.Thread(target=file_worker)
        t.daemon = True
        t.start()
        files_workers.append(t)

    full_folder_backup(start_dir)

    try:
        while True:
            if not files_to_process:
                system('cls')
                print('Waiting for new files.')
                time.sleep(1)
                system('cls')
                print('Waiting for new files..')
                time.sleep(1)
                system('cls')
                print('Waiting for new files...')
                time.sleep(1)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('Terminating Script, waiting Job to finish')
        observer.stop()
        
        observer.join()  # Wait for the observer to finish
        folder_process_queue.all_tasks_done
        #file_process_queue.all_tasks_done
        
    finally:
        system('cls')
        print('Script Terminated.. ')
    