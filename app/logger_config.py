import logging
import sys

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(levelname)s[%(name)s]: %(message)s")

    handler.setFormatter(formatter)

    if not root_logger.handlers:
        root_logger.addHandler(handler)
