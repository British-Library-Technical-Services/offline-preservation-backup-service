"""Backup reporting utilities.

This module is responsible for producing a human‑readable Markdown summary of a
backup run executed by the preservation backup service. The generated report
captures timing, file counts, checksum activity, skipped and invalid files,
and aggregate data size. Reports are written to the backup destination.

Environment variables:
    BACKUP_LOCATION: Directory where the Markdown report will be created.

Exports:
    write_report(...): Persist a formatted backup report to BACKUP_LOCATION.
"""

import os

write_location = os.getenv("BACKUP_LOCATION")


def write_report(
    start_time,
    end_time,
    duration,
    total_files,
    copied_files,
    checksums_generated,
    skipped_files,
    total_size,
    invalid_files,
):
    """Write a Markdown report summarising a completed backup run.

    Args:
        start_time (datetime): When the backup process began.
        end_time (datetime): When the backup process ended.
        duration (timedelta): Elapsed wall-clock time (end - start).
        total_files (int): Count of source files encountered (incl. skipped).
        copied_files (int): Number of files successfully copied.
        checksums_generated (list[Path | str]): Newly created checksum files.
        skipped_files (list[Path | str]): Files found already present in backup.
        total_size (float): Aggregate size in MB of copied data.
        invalid_files (list[Path | str]): Files whose checksum validation failed.

    Side Effects:
        Writes a file named backup_report_<timestamp>.md into BACKUP_LOCATION.

    Notes:
        The timestamp in the filename is derived from end_time.
    """

    report = f"""
# BACKUP REPORT

* Backup started on {start_time} 
* Backup ended on {end_time}
* Total time: {duration}
* Total no of files on source: {total_files}
* Total no of files backed up: {copied_files}
* Total no of new checksums generated: {len(checksums_generated)}
* Total no of files skipped: {len(skipped_files)}
* Total size of data backed up: {total_size:.2f} MB
* files INVALID: {len(invalid_files)}
    
    """
    if len(invalid_files) > 0:
        report += "INVALID FILES\n"
        for f in invalid_files:
            report += f"    * {f}\n"

    end_time = end_time.strftime("%Y-%m-%d_%H-%M-%S")
    with open(os.path.join(write_location, f"backup_report_{end_time}.md"), "w", encoding="utf-8") as f:
        f.write(os.path.join(report))
