# wrapper around logger for easy instantiation across 

import logging

def get_logger(name='BatteryTest'):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fname = name + '.log'
    fh = logging.FileHandler(fname)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    # return logger
    return logger

if __name__ == '__main__':
    logger = get_logger('Test ')
    logger.debug('test debug')
    logger.info('test info')
    logger.warning('test warning')
    logger.error('test error')
    logger.critical('test critical')
