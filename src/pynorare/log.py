import logging
logging.basicConfig(level=logging.INFO)

_logger = None


def get_logger():
    global _logger
    if not _logger:
        _logger = logging.getLogger('[norare] ')
    return _logger
