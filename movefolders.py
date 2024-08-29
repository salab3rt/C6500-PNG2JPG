#import shutil
#import os
#from pathlib import Path
#
#src_dir = Path('X:\\backup\\2023')
#
#
#for folder in src_dir.iterdir():
#    if folder.is_dir() and folder.name != 'backup':
#        sample_name = folder.name.split('_')[2]
#        if sample_name[-1:] == 'R':
#            sample_folder_name = sample_name if sample_name[-4:] not in ['600R', '800R', '150R', '809R', '899R'] else sample_name[0:len(sample_name) -4]
#        else:
#            sample_folder_name = sample_name if sample_name[-3:] not in ['600', '800', '150', '809', '899'] else sample_name[0:len(sample_name) -3]
#        new_folder = src_dir / sample_folder_name
#        new_folder.mkdir(parents=True, exist_ok=True)
#        #print(new_folder)
#        #print(folder)
#        shutil.move(folder, new_folder)

import shutil
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

src_dir = Path('X:\\backup\\2024')

folder_list = list(src_dir.iterdir())

def move_folder(folder):
    if folder.is_dir() and folder.name != 'backup':
        sample_parts = folder.name.split('_')

        if len(sample_parts) > 2:
            sample_name = sample_parts[2]
            if sample_name[-1:] == 'R':
                sample_folder_name = sample_name if sample_name[-4:] not in ['600R', '800R', '150R', '809R', '899R'] else sample_name[0:len(sample_name) -4]
            else:
                sample_folder_name = sample_name if sample_name[-3:] not in ['600', '800', '150', '809', '899'] else sample_name[0:len(sample_name) -3]
            new_folder = src_dir / sample_folder_name
            new_folder.mkdir(parents=True, exist_ok=True)
            shutil.move(str(folder), str(new_folder))  # Convert Path objects to strings for shutil


with ThreadPoolExecutor(max_workers=6) as executor:  # Adjust the number of workers as needed
    executor.map(move_folder, folder_list)