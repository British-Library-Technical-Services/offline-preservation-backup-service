import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from logger import logger
from report import write_report

SOURCE_LOCATION = os.getenv("SOURCE_LOCATION")
BACKUP_LOCATION = os.getenv("BACKUP_LOCATION")

source_files = []
checksums_generated = []
skipped_files = []
invalid_files = []

def checksum_validate(file_checksum, md5_hash):
    if file_checksum == md5_hash:
        return True
    else:
        return False


def md5_write(file, file_checksum):
    filename = os.path.basename(file).replace(".md5", "")

    try:
        with open(file, "w") as f:
            f.write(f"{file_checksum} *{filename}")
    except OSError as e:
        logger.error(e)


def md5_generate(file):
    try:
        with open(file, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

            return file_hash.hexdigest()

    except OSError as e:
        logger.error(e)


def md5_read(file):
    try:
        with open(file, "r") as f:
            return f.read(32)
    except OSError as e:
        logger.error(e)


def file_copy(src, dst):
    try:
        shutil.copy2(src, dst)
        logger.info(f"copied file,{src},{dst}")
    except OSError as e:
        logger.error(e)


def directory_write(directory):
    try:
        os.mkdir(os.path.join(directory))
    except OSError as e:
        logger.error(e)


start_time = datetime.now()
logger.info(f"backup started,{start_time}")

print("---| Full Backup in Progress. Please wait... |---")

size_stat = 0

for root in tqdm(sorted(Path(SOURCE_LOCATION).rglob("*")), desc="IN PROGRESS"):


    source = str(SOURCE_LOCATION)
    source_path = str(root)
    backup = str(root).replace(SOURCE_LOCATION, BACKUP_LOCATION)

    if str(root).endswith(".md5"):
        pass

    elif os.path.isdir(root) and not os.path.exists(backup):
        logger.info(f"writing directory,{backup}")
        directory_write(backup)
        pass

    elif os.path.isfile(root) and os.path.basename(root).startswith("."):
        pass

    elif (
        os.path.isfile(root)
        and not str(root).endswith(".md5")
        and not os.path.exists(backup)
    ):
        source_files.append(root)

        md5_file = f"{root}.md5"

        if not os.path.exists(md5_file):
            file_checksum = md5_generate(root)
            md5_write(md5_file, file_checksum)
            logger.info(f"generated checksum,{root},{file_checksum}")

            checksums_generated.append(md5_file)


        file_copy(md5_file, f"{backup}.md5")
        file_copy(root, backup)
        size_stat += root.stat().st_size

        file_checksum = md5_generate(backup)
        md5_file = f"{backup}.md5"

        if not checksum_validate(file_checksum, md5_read(md5_file)):
            logger.critical(f"checksum INVALID,{root},{file_checksum}")
            invalid_files.append(root)
            os.remove(backup)
            os.remove(md5_file)
            logger.warning(f"removed invalid file from backup,{backup}")
        else:
            logger.info(f"checksum VALID,{root},{file_checksum}")

    elif os.path.isfile(root) and os.path.exists(backup):
        logger.info(f"{root} exists in {backup}. SKIPPING file")
        skipped_files.append(root)

    else:
        pass

end_time = datetime.now()
duration = end_time - start_time
total_files = len(source_files) + len(skipped_files)
copied_files = total_files - len(skipped_files) - len(invalid_files)
total_size = size_stat / (1024 ** 2)

write_report(
    start_time,
    end_time,
    duration,
    total_files,
    copied_files,
    checksums_generated,
    skipped_files,
    total_size,
    invalid_files,
)

logger.info(f"backup completed,{end_time}")
logger.info(f"backup duration,{duration}")
