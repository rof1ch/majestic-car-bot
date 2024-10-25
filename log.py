import logging
import os
from datetime import datetime


class Logger:
    def __init__(self):
        app_level = os.getenv("LEVEL")
        if app_level == "dev":
            logging.basicConfig(
                level=logging.DEBUG,
                filename="bot.dev.log",
                filemode="w",
                format="%(asctime)s %(levelname)s %(message)s",
            )
        elif app_level == "prod":
            logging.basicConfig(
                level=logging.INFO,
                filename="bot.log",
                filemode="w",
                format="%(asctime)s %(levelname)s %(message)s",
            )

    def log(self, level: int, message: str):
        """
        1 - Debug \n
        2 - Info \n
        3 - Warning \n
        4 - Error \n
        5 - Critical \n
        """
        match level:
            case 1:
                print(f"DEBUG: {datetime.now()} - {message}")
                logging.debug(message)
            case 2:
                print(f"INFO: {datetime.now()} - {message}")
                logging.info(message)
            case 3:
                print(f"WARNING: {datetime.now()} - {message}")
                logging.warning(message)
            case 4:
                print(f"ERROR: {datetime.now()} - {message}")
                logging.error(message)
            case 5:
                print(f"ERROR: {datetime.now()} - {message}")
                logging.critical(message)
