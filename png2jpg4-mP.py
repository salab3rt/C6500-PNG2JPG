import queue
import multiprocessing
import sqlite3
from pathlib import Path
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import time
from datetime import datetime


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

main_conn = sqlite3.connect('database.db', check_same_thread=False)
cur = main_conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS processed_files (file_path TEXT PRIMARY KEY)')
main_conn.commit()
cur.close()

# Create a queue to store the folders that need to be processed
process_queue = queue.Queue()


def is_folder_processed(folder_path, file_count=0):
    try:
        with main_conn:
            cur = main_conn.cursor()
            cur.execute('SELECT * FROM processed_files WHERE file_path LIKE ?', (str(folder_path) + '%',))
            row = cur.fetchall()
            cur.close()
            if row and len(row) >= file_count:
                return True
            else:
                return False
    except Exception as e:
        logger.error(f'SQLite Error: {e}')


def get_file_count_in_folder(folder_path):
    return sum(1 for _ in folder_path.glob('*.png'))

# Add the existing folders to the queue
with main_conn:
    print(datetime.now())
    for folder in start_dir.iterdir():
        if folder.is_dir():
            file_count = get_file_count_in_folder(folder)
            if not is_folder_processed(folder, file_count=file_count):
                process_queue.put(folder)


def save_db_record(records, conn):
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO processed_files (file_path) VALUES (?)', (str(records),))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error(f'SQLite Error: {e}')


def process_file(file_path):
    try:
        with sqlite3.connect('database.db') as conn:
            if file_path.is_file() and file_path.suffix.lower() == '.png':
                convert_and_backup(file_path)

                full_path = file_path.parent / file_path.name
                save_db_record(full_path, conn)

            elif file_path.is_dir():
                for file in file_path.iterdir():
                    # print("FILE:",file)
                    if file.is_file() and file.suffix.lower() == '.png':
                        convert_and_backup(file)

                        full_path = file_path / file.name
                        save_db_record(full_path, conn)

    except Exception as e:
        print(e)
        logger.error(f'Error processing {file_path}: {e}')

def convert_and_backup(file_path):
    # print(file_path)
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

                year = datetime.now().year
                dest_path = backup_dir / str(year) / custom_folder_name / file_path.name
                dest_path = dest_path.with_suffix('.jpg')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(dest_path)

                # logger.info(f'Converted file: {file_path}')

        except Exception as e:
            logger.error(f'Error processing {file_path}: {e}')


class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        try:
            if not event.is_directory:
                file_path = Path(event.src_path)
                if file_path.suffix.lower() == '.png':
                    file_count = get_file_count_in_folder(file_path.parent)
                    if not is_folder_processed(file_path.parent, file_count=file_count):
                        process_queue.put(file_path)
                        logger.info(f'Added to queue: {file_path}')
                        time.sleep(0.5)
        except Exception as e:
            logger.error(f'Event Error: {e}, Event: {event}')


if __name__ == "__main__":
    # Setup logger
    logger = setup_logging()

    # Use multiprocessing instead of multithreading
    pool = multiprocessing.Pool(processes=4)

    # Start monitoring the folder for new files
    event_handler = FileHandler()
    observer = Observer(timeout=0.5)
    observer.schedule(event_handler, path=start_dir, recursive=True)
    observer.start()

    try:
        while True:
            # The next line utilizes the pool to process the tasks from the queue
            tasks = [process_queue.get() for _ in range(min(process_queue.qsize(), 4))]
            pool.map(process_file, tasks)
            for _ in tasks:
                process_queue.task_done()
                print(datetime.now())
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        pool.close()
        pool.terminate()
        pool.join()
        main_conn.close()