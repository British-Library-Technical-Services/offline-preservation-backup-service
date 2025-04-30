#from Typing import Path
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
# from report import write_report

class PreservationBackupService:
    def __init__(self, file: str, source_path: str, backup_path: str) -> None:
        self.file: Path = file
        self.md5_file: str = f"{file}.md5"
        self.md5_string: str = ""
        self.source_path: str = source_path
        self.backup_path: str = backup_path
        self.backup_file: str = os.path.join(os.path.dirname(file).replace(source_path, backup_path), os.path.basename(file))
        self.backup_md5_file: str = os.path.join(os.path.dirname(file).replace(source_path, backup_path), os.path.basename(self.md5_file))
    
    def is_backup_eligible(self) -> bool:
        try:
            if os.path.splitext(self.file)[1] == ".md5":
                return False

            elif os.path.isfile(self.file) and os.path.basename(self.file).startswith("."):
                return False

            elif os.path.isdir(self.file) and not os.path.exists(self.backup_file):
                self.write_directory_in_backup()
                return False

            elif os.path.isfile(self.file) and not os.path.exists(self.md5_file):
                return True
            
        except (AttributeError, TypeError) as e:
            raise TypeError(f"Error processing file {self.file}: {e}") from e
        
        except OSError as e:
            raise OSError(f"Error accessing files: {self.file}: {e}") from e

    def write_directory_in_backup(self) -> None:
        try:
            os.mkdir(self.backup_file)
        except OSError as e:
            raise OSError(f"Error accessing files: {self.backup_file}: {e}") from e

    def generate_file_checksum(self, file) -> None:
        file_hash: hash = hashlib.md5()
        try:
            with open(file, "rb") as f:
                while buffer := f.read(8196):
                    file_hash.update(buffer)
            
            self.md5_string = file_hash.hexdigest()

        except (OSError) as e:
            raise OSError(f"Error accessing files: {self.file}: {e}") from e
    
    def write_checksum_file(self) -> None:
        try:
            with open(self.md5_file, "w", encoding="utf-8") as f: # f: TextIO
                f.write(f"{self.md5_string} *{os.path.basename(self.file)}")
        
        except OSError as e:
            raise OSError("Error writing .md5 checksum file: {self.md5_file}:  {e}") from e
        
    def copy_file_to_backup(self) -> bool:
        if not os.path.exists(self.backup_file) and not os.path.exists(self.backup_md5_file):
            try:
                shutil.copyfile(self.file, self.backup_file)
            except OSError as e:
                raise OSError(f"Error copying {self.file} to backup: {e}") from e
            try:
                shutil.copyfile(self.md5_file, self.backup_md5_file)
            except OSError as e:
                raise OSError(f"Error copying {self.md5_file} to backup: {e}") from e
        else:
            # return (f"{self.file} exists in backup location.  Skipping copy")
            return False
    
    def read_file_checksum(self) -> str:
        try:
            with open(self.backup_md5_file, "r", encoding="utf-8") as f:
                checksum_file_string: str = f.read(32)

            return checksum_file_string
        except OSError as e:
            raise OSError(f"Error reading .md5 checksum file: {self.backup_md5_file}: {e}") from e
          
            
    def validate_file_checksum(self: str) -> bool:
        if os.path.exists(self.backup_file):
            self.generate_file_checksum(file=self.backup_file)
            checksum_file_string = self.read_file_checksum()
            
            if not self.md5_string == checksum_file_string:
                return False
            else:
                return True 

def set_location() -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:        
        location: str = filedialog.askdirectory(initialdir="~")
    except FileNotFoundError as fnfe:
        print("Error opening directory selection dialog %s. Exiting", fnfe)
        sys.exit(1)
    finally:
        root.destroy()

    if not os.path.exists(location) or location == "":
        print("Path location does not exist. Exiting")
        sys.exit(1)
    else:
        return location


def main():
    verified_files: list[str] = []
    failed_files: list[str] = []
    skipped_files: list[str] = []

    # source_location: str = set_location()
    # backup_location: str = set_location()
    source_location: str = "/media/soundarchive/3604/C1979"
    backup_location: str = "/media/soundarchive/3604/backup_copy_tests"

    logger = setup_logger(write_location=source_location)

    start_time: datetime = datetime.now()

    for item in tqdm(sorted(Path(source_location).rglob("*")), desc="FUll Backup in Progress"):
        try:
            pbs = PreservationBackupService(file=item, source_path=source_location, backup_path=backup_location)
            file_to_copy = pbs.is_backup_eligible()

            if file_to_copy:
                pbs.generate_file_checksum(file=item)
                pbs.write_checksum_file()
            
            copy_status = pbs.copy_file_to_backup()
                    
                # if isinstance(copy_status, str) and "exists" in copy_status:
                if not copy_status:
                    logger.info("%s exists in backup location: copy skipped", item) 
                    skipped_files.append(item)

                valid_checksum = pbs.validate_file_checksum()
                if not valid_checksum:
                    logger.critical("Failed checksum validation: %s", item)
                    failed_files.append(item)
            else:
                verified_files.append(item)
        
        except TypeError as e:
            logger.error("TypeError: %s", e)
            continue
        except OSError as e:
            logger.error("OSError: %s", e)
            continue
        except Exception as e:
            logger.error("Unexpected error: %s", e)

    end_time: datetime = datetime.now()
    duration = end_time - start_time

    logger.info("Backup started: %s, ended: %s, duration: %s, verified checksums: %d, failed checksums: %d, files skipped: %d",
                start_time, end_time, duration, len(verified_files), len(failed_files), len(skipped_files))
    
    print(f"Backup started: {start_time}, ended: {end_time}, duration: {duration}, verified checksums: {len(verified_files)}, failed checksums: {len(failed_files)}, files skipped: {len(skipped_files)}")
    
    if len(failed_files) > 0:
        print(f"ERROR: files failed verification: {failed_files}")

if __name__ == "__main__":
    main()