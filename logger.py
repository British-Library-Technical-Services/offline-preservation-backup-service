import os
from datetime import datetime
import logging

def setup_logger(write_location: str):
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s:%(module)s:%(levelname)s:%(message)s",
        handlers = [
            logging.FileHandler(os.path.join(write_location, "backup.log")),
        ]
    )

    logger = logging.getLogger(__name__)
    return logger