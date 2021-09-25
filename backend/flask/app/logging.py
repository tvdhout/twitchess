import logging
from logging.handlers import RotatingFileHandler

__all__ = ['get_logger']


def get_logger(name: str, level: str = 'INFO', max_file_size: int = int(2e6)) -> logging.Logger:
    logger = logging.getLogger(name)

    file_handler = RotatingFileHandler(f'/logging/{name}.log', maxBytes=max_file_size)
    file_formatter = logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s', '%Y-%m-%d %H:%M')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter(f'%(asctime)s [{name}] [%(levelname)s]: %(message)s', '%Y-%m-%d %H:%M:%S')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(level)
    return logger
