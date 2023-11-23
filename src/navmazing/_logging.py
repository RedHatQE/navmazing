import logging

null_logger = logging.getLogger("navmazing.null")
null_logger.addHandler(logging.NullHandler())
