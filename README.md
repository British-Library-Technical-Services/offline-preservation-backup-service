# Offline Preservation Backup Service

Automated, integrity‑verifying backup tool that mirrors a source directory tree
to a designated backup location while generating and validating MD5 checksum
sidecar files. Produces structured logs and a Markdown summary report for each
run (including counts, sizes, and any integrity failures).

This service is run to create a full backup of the working RAID array for offline data preservation

## Features

- Recursive full backup (directory structure preserved)
- MD5 checksum generation (.md5 sidecar files in coreutils format)
- Post‑copy checksum validation (integrity enforcement)
- Skips existing files already present at the destination
- Structured logging to `backup.log`
- Markdown report of each run with statistics & invalid file listing

## How It Works

1. Walk the `SOURCE_LOCATION` tree.
2. Create any missing directories in `BACKUP_LOCATION`.
3. For each regular file (excluding dotfiles & existing `.md5` files):
	- Generate a checksum file alongside the source if missing.
	- Copy the file and its checksum to the mirrored path.
	- Recompute checksum from the copied file and compare to sidecar.
	- Delete copied artifacts if the validation fails.
4. Gather metrics and write a human‑readable report.

## Requirements

- Python 3.9+ (tested on macOS)
- Packages: `tqdm`

Install dependencies (if using a virtual environment):

```bash
pip install tqdm
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SOURCE_LOCATION` | Absolute path of source directory tree to back up | Yes |
| `BACKUP_LOCATION` | Absolute path of destination backup directory | Yes |

Both paths must exist and be readable (source) / writable (backup) prior to running.

## Running a Backup

From the repository root:

```bash
export SOURCE_LOCATION="/path/to/source" \
		 BACKUP_LOCATION="/path/to/backup"

python preservation_backup.py
```

You will see a progress bar and log entries will accumulate in:

```
$BACKUP_LOCATION/backup.log
```

At completion a Markdown report is written to:

```
$BACKUP_LOCATION/backup_report_<timestamp>.md
```

## Output Artifacts

- `backup.log`: Structured CSV‑like log lines: `timestamp:module:level:message`
- `.md5` files: Sidecar checksum files (format: `<checksum> *<filename>`)
- `backup_report_<timestamp>.md`: Summary metrics and invalid file list

## Report Contents

The report includes:

- Start/end time and duration
- Total files encountered vs copied
- New checksum files generated
- Skipped existing files
- Total data volume copied (MB)
- Count and list of invalid (failed checksum) files


