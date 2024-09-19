import os
from datetime import datetime
import logging

LOG_WRITE_LOCATION = os.getenv("BACKUP_LOCATION")

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s:%(module)s:%(levelname)s:%(message)s",
    handlers = [
        logging.FileHandler(os.path.join(LOG_WRITE_LOCATION, "backup.log")),
    ]
)

logger = logging.getLogger(__name__)