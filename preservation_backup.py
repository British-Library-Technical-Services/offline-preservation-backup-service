"""Offline preservation backup service.

Copies all files from the source preservation directory to a designated backup
location while generating and validating MD5 checksum sidecar files (.md5).

Workflow overview:
1. Recursively iterate through SOURCE_LOCATION.
2. For every directory missing in BACKUP_LOCATION, create it.
3. For every regular file (excluding dotfiles and existing .md5 files):
   - Generate a checksum file alongside the source if one does not exist.
   - Copy the file and its checksum to the backup tree (mirrored path).
   - Recalculate the checksum from the copied file and validate it against
     the copied .md5 sidecar; if invalid, remove the copied artifacts.
4. Collect statistics (counts, sizes, skipped, invalid) and emit a report.

Environment variables:
    SOURCE_LOCATION: Absolute path to source directory tree to back up.
    BACKUP_LOCATION: Absolute path to destination (backup) directory tree.

Exports:
    main(): Entrypoint for executing a full backup run.

Logging: Structured / CSV‑style messages emitted via logger for audit trails.
Report: A human / machine readable report is written via report.write_report.
"""

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
    """Return True if a newly generated checksum matches the stored hash.

    Args:
        file_checksum (str): Newly generated checksum value (hex string).
        md5_hash (str): Stored reference MD5 hash (hex string) to compare to.

    Returns:
        bool: True when both values are identical, else False.
    """
    if file_checksum == md5_hash:
        return True
    else:
        return False


def md5_write(file, file_checksum):
    """Write a checksum value to a .md5 sidecar file.

    Format written: "<checksum><space>*<filename>".

    Args:
        file (str | Path): Path to the checksum file to create/overwrite.
        file_checksum (str): Hexadecimal MD5 digest.
    """
    filename = os.path.basename(file).replace(".md5", "")
    try:
        with open(file, "w") as f:
            f.write(f"{file_checksum} *{filename}")
    except OSError as e:
        logger.error(e)


def md5_generate(file):
    """Generate an MD5 checksum for a file streaming in fixed-size chunks.

    Args:
        file (str | Path): File whose digest should be computed.

    Returns:
        str | None: Hex digest on success, None if an OS error occurred.
    """
    try:
        with open(file, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except OSError as e:
        logger.error(e)


def md5_read(file):
    """Read the first 32 characters (MD5 hex digest) from a .md5 file.

    Args:
        file (str | Path): Path to a checksum sidecar.

    Returns:
        str | None: 32‑char hex digest, or None if read failed.
    """
    try:
        with open(file, "r") as f:
            return f.read(32)
    except OSError as e:
        logger.error(e)


def file_copy(src, dst):
    """Copy a file preserving metadata (copy2) and log the operation.

    Args:
        src (str | Path): Source file path.
        dst (str | Path): Destination file path (directories must exist).
    """
    try:
        shutil.copy2(src, dst)
        logger.info(f"copied file,{src},{dst}")
    except OSError as e:
        logger.error(e)


def directory_write(directory):
    """Create a single directory (non-recursive) and log failures.

    Args:
        directory (str | Path): Directory path to create. Parents must exist.
    """
    try:
        os.mkdir(os.path.join(directory))
    except OSError as e:
        logger.error(e)


def main():
    """Execute a full backup run.

    Traverses SOURCE_LOCATION mirroring structure to BACKUP_LOCATION while
    creating / validating checksums and gathering statistics. Results are
    written via write_report and progress is logged.
    """

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
    total_size = size_stat / (1024**2)

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


if __name__ == "__main__":
    main()
