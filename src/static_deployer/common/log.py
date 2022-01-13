import inspect
import logging
import sys

logger = logging.getLogger(__name__)


def _make_debug_record(message):
    fn, lno, func, sinfo = logger.findCaller()
    record = logger.makeRecord(logger.name, logging.DEBUG, fn, lno, message, None, None,
                               func=func, extra=None, sinfo=sinfo)
    return record


def debug(message: str):
    record = _make_debug_record(message)
    logger.handle(record)
