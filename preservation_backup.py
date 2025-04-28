import sys
import os
import shutil
import hashlib 
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from datetime import datetime

from tqdm import tqdm

from logger import setup_logger
from report import write_report

class PreservationBackupService:
    def __init__(self, file: str, source_path: str, backup_path: str) -> None:
        print(source_path, backup_path)
        self.file: str = file
        self.md5_file: str = f"{file}.md5"
        self.md5_string: str = ""
        self.source_path: str = source_path
        self.backup_path: str = backup_path
        self.backup_file: str = file.replace(source_path, backup_path)
        self.backup_md5_file: str = self.md5_file.replace(source_path, backup_path) # BUG: need to correctly resolve path object
    
    def parse_file_type(self) -> None:
        if self.file.endswith(".md5"):
            pass

        elif os.path.isfile(self.file) and self.file.startswith("."):
            pass

        elif os.path.isdir(self.file) and not os.path.exists(self.backup_file):
            self.write_directory_in_backup()

        elif os.path.isfile(self.file) and not os.path.exists(self.md5_file):
            self.generate_file_checksum(file=self.file)
            self.write_checksum_file()

    def write_directory_in_backup(self):
        try:
            os.mkdir(self.backup_file)
        except OSError as ose:
            return ose

    def generate_file_checksum(self, file):
        file_hash: hash = hashlib.md5()

        try:
            with open(file, "rb") as f:
                while buffer := f.read(8128):
                    file_hash.update(buffer)
            
            self.md5_string = file_hash.hexdigest()
        except FileNotFoundError as fnfe:
            return fnfe
        except IOError as ioe:
            return ioe
    
    def write_checksum_file(self):
        try:
            with open(self.md5_file, "w", encoding="utf-8") as f: # f: TextIO
                f.write(f"{self.md5_string} *{os.path.basename(self.file)}")
        
        except FileNotFoundError as fnfe:
            return fnfe
        except IOError as ioe:
            return ioe
        
    def copy_file_to_back(self) -> None:

        if not os.path.exists(self.backup_file) and not os.path.exists(self.backup_md5_file):
            shutil.copy2(self.file, self.backup_file)
            shutil.copy2(self.md5_file, self.backup_md5_file)
        else:
            # log file exists in backup
            pass

    
    def read_file_checksum(self, file_checksum_string: str) -> bool:
        try:
            with open(self.backup_md5_file, "r", encoding="utf-8") as f:
                checksum_file_string: str = f.read(32)
        except FileNotFoundError as fnfe:
            return fnfe
        except IOError as ioe:
            return ioe
            
        if not file_checksum_string == checksum_file_string:
            return False
        else:
            return True 
    

    def validate_file_checksum(self):
        source_file_checksum: str = self.md5_string

        if os.path.exists(self.backup_file):
            self.generate_file_checksum(file=self.backup_file)
            self.read_file_checksum(file_checksum_string=source_file_checksum)
            

def set_location() -> str:
    window = tk.Tk()
    window.attributes("-topmost", True)

    try:        
        location: str = filedialog.askdirectory(initialdir="~/media/")
    except FileNotFoundError as fnfe:
        print("Error opening directory selection dialog %s. Exiting", fnfe)
        sys.exit(1)

    if not os.path.exists(location) or location == "":
        print("Path location does not exist. Exiting")
        sys.exit(1)
    else:
        return location


def main():
    source_location: str = set_location()
    backup_location: str = set_location()

    for item in tqdm(sorted(Path(source_location).rglob("*")), desc="FUll Backup in Progress"):
        pbs = PreservationBackupService(file=item, source_path=source_location, backup_path=backup_location)
        pbs.parse_file_type()
        pbs.copy_file_to_back()
        pbs.validate_file_checksum()


if __name__ == "__main__":
    main()