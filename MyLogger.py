import logging

# create logger
logger = logging.getLogger('simple_logger')
logger.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s | %(levelname)8s | %(filename)s:%(funcName)s:%(lineno)d |  %(message)s')

# command line logger
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# file logger
fh = logging.FileHandler('./logs/log1.txt')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)