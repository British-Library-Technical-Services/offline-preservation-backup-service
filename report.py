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
    with open(os.path.join(write_location, f"backup_report_{end_time}.md"), "w") as f:
        f.write(os.path.join(report))
