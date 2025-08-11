"""Central logging configuration for the offline preservation backup service.

This module configures a process‑wide logging setup writing INFO and above
messages to a rotating (single) log file located in the backup destination
directory. The file path is resolved from the BACKUP_LOCATION environment
variable and the log file is named ``backup.log``.

Log format:
    ``timestamp:module:level:message`` (as produced by logging.basicConfig)

Environment variables:
    BACKUP_LOCATION: Destination directory where ``backup.log`` will be written.

Exports:
    logger (logging.Logger): Preconfigured logger for use across modules.

"""

import os
from datetime import datetime
import logging

LOG_WRITE_LOCATION = os.getenv("BACKUP_LOCATION")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(module)s:%(levelname)s:%(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_WRITE_LOCATION, "backup.log")),
    ],
)

logger = logging.getLogger(__name__)
