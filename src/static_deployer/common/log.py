import logging
import multiprocessing
import multiprocessing_logging
import os

log_level_from_env = os.environ.get('LOGLEVEL', '').upper()
log_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(funcName)s %(message)s'
log_level = logging.DEBUG if log_level_from_env == 'DEBUG' else logging.INFO

logging.basicConfig(format=log_format, level=log_level)
logger = logging.getLogger(__name__)

mp_logger = multiprocessing.get_logger()
# mp_handler = logging.StreamHandler()
# mp_handler.setLevel(log_level)
# mp_handler.setFormatter(logging.Formatter(log_format))
# mp_logger.addHandler(mp_handler)

# Handle records from parallel processes to the main process so that they are handled correctly.
multiprocessing_logging.install_mp_handler()

def _make_debug_record(message):
    fn, lno, func, sinfo = logger.findCaller()
    record = logger.makeRecord(logger.name, logging.DEBUG, fn, lno, message, None, None,
                               func=func, extra=None, sinfo=sinfo)
    return record


def debug(message: str):
    record = _make_debug_record(message)
    logger.handle(record)
