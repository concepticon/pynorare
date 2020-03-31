import logging
logging.basicConfig(level=logging.INFO)

def get_logger():
    global _logger
    _logger = logging.getLogger('[norare] ')
    return _logger


def info(msg, **kw):
    get_logger().info(' '+msg, **kw)


def warning(msg, **kw):
    get_logger().warning(' '+msg)


def loaded(msg, **kw):
    get_logger().info(" Loaded the file {0}.".format(msg))


def matches(msg, **kw):
    get_logger().info(" Found {0} matches in data.".format(msg), **kw)


def download(msg, **kw):
    get_logger().info(" Downloaded {0} successfully.".format(msg), **kw)


def written(msg, **kw):
    get_logger().info(" File {0} successfully written.".format(msg), **kw)
