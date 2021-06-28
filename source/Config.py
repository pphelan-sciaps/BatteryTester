# imports
import logging
from datetime import datetime

# program wide config and constants
VERSION = '0.1.2'

# logfile
def logger_init(fname=None):
    # create logger and set level
    logger = logging.getLogger('batman')
    logger.setLevel(logging.DEBUG)

    # build filename (multiple instances may be running at once)
    if not fname:
        fname = f'logs/batman_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'

    # format output
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # create log file handler and configure
    fh = logging.FileHandler(fname)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create log console handler and configure
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info('logfile created')