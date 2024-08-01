import queue
import threading
import win32file
import win32con
from pathlib import Path
from os import system, access, R_OK
from PIL import Image
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
        try:
            if folder.is_dir() and folder.name != 'backup':
                #with files_lock:
                    #files_to_process.add(folder)
                files_lock.acquire(blocking=True, timeout=2)
                files_queue.put(folder, timeout=2)
                files_lock.release()
                
        except Exception as e:
                    logger.error(f'Error reading {folder}: {e}')
        finally:
            continue


def is_readable(file_path, max_wait_seconds=5, sleep_duration=0.001):
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
        if path.is_dir():
            with tqdm(total=get_file_count_in_folder(path), desc=f'{path.name[17:]}', unit='files', bar_format="{desc} |{bar}| [{n_fmt}/{total_fmt}] {elapsed} |", leave=False) as pbar:
                for file in path.iterdir():
                    if file.suffix.lower() == '.png' and not is_processed(file):
                        convert_and_backup(file)
                    pbar.update(1)
                pbar.close
            #system('cls')
            return True

        elif path.is_file():
            with tqdm(total=1, desc=f'{path.name}', unit='file', leave=True, position=0, bar_format="{desc} |{bar}| {elapsed} ") as pbar:
                processed_file = convert_and_backup(path)
                pbar.update(1)
            pbar.close
            if processed_file:
                return processed_file
            else:
                return None
            
        else:
            logger.error(f'Error processing {path}')
            return None
                                
    except Exception as e:
        print(e)
        logger.error(f'Error processing {path}: {e}')
        return None

            
def monitor_directory(directory):
    FILE_LIST_DIRECTORY = 0x0001
    hDir = win32file.CreateFile(
        directory,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )
    try:
        while not terminate_flag.is_set():
            results = win32file.ReadDirectoryChangesW(
                hDir,
                16384,
                True,
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME|
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_SIZE |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
                None,
                None
            )

            for action, file_name in results:
                full_file_path = Path(directory) / file_name
                if action == 1:  # File Created
                    if str(backup_dir)not in str(full_file_path) and full_file_path.suffix.lower() == '.png':
                        #with files_lock:
                            #files_to_process.add(full_file_path)
                        files_lock.acquire(blocking=True, timeout=2)
                        files_queue.put(full_file_path)
                        files_lock.release()
                    else:
                        pass
                elif action == 2:  # File Deleted
                    # Handle file deletion if needed
                    pass
                # Add handling for other actions as needed
    except Exception as e:
        logger.error(f'Handler error: {e}')


def file_worker():
    max_retries = 20

    while True:
        try:
            time.sleep(.01)
            #if len(files_to_process) > 0:
            if not files_queue.empty():
                #with files_lock:
                    #file_path = files_to_process.pop()
                files_lock.acquire(blocking=True, timeout=2)
                file_path = files_queue.get(timeout=2)
                files_lock.release()
                if file_path:
                    retries = 0
                    while retries < max_retries:
                        processed_file = process_file(file_path)
                        if not processed_file:
                            retries += 1
                            logger.warning(f"Processing failed for {file_path}. Retrying attempt {retries}/{max_retries}")
                        else:
                            break  # Break out of the retry loop on successful processing
                    if retries == max_retries:
                        files_lock.acquire(blocking=True, timeout=2)
                        files_queue.put(file_path, timeout=2)
                        files_lock.release()
                        logger.error(f"Max retries reached. Returning {file_path} to queue.")
                #files_queue.task_done()
                    
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
        if is_readable(file_path):
            with Image.open(file_path, 'r') as img:
                img = img.convert('RGB')
                new_width = img.width // 2
                new_height = img.height // 2
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                year = datetime.now().year
                dest_path = backup_dir / str(year) / custom_folder_name / file_path.name
                dest_path = dest_path.with_suffix('.jpg')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path)

            return True
            #logger.info(f'Converted file: {file_path}')

    # Handle this specific permission error case
    except Exception as e:
        logger.error(f'Error reading {file_path}: {e}')
        return False


if __name__ == "__main__":
    
    terminate_flag = threading.Event()
    
    just_fix_windows_console()
    print('Starting BACKUP Script')
    
    # Define the paths
    start_dir = Path('X:')
    #start_dir = Path('./imgs')

    backup_dir = start_dir / 'backup'

    backup_dir.mkdir(parents=True, exist_ok=True)

    files_queue = queue.Queue(maxsize=-1)
    #files_to_process = set(range(200000))
    files_lock = threading.Lock()
    
    #Setup logger
    logger = setup_logging()
    
    monitor_thread = threading.Thread(target=monitor_directory, args=(str(start_dir),), daemon=True)
    monitor_thread.start()

    files_workers = []
    for i in range(6):
        t = threading.Thread(target=file_worker)
        t.daemon = True
        t.start()
        files_workers.append(t)

    full_folder_backup(start_dir)

    try:
        while not terminate_flag.is_set():
            if not not files_queue.empty():
            #if not len(files_to_process) > 0:
                system('cls')
                print('Waiting for new files.')
                time.sleep(1)
                if not not files_queue.empty():
                #if not len(files_to_process) > 0:
                    system('cls')
                    print('Waiting for new files..')
                    time.sleep(1)
                if not not files_queue.empty():
                #if not len(files_to_process) > 0:
                    system('cls')
                    print('Waiting for new files...')
                    time.sleep(1)

            #else:
            #    system('cls')
            #    print(' Processing new files... \n')
                
            time.sleep(0.5)
    except KeyboardInterrupt:
        #files_queue.join()
        terminate_flag.set()
        
        system('cls')
        print('Terminating Script, waiting Job to finish')
        
    finally:

        system('cls')
        print('Script Terminated.. ')
    