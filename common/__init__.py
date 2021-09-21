import os
import logging

#
# Logging
#
LOG_FORMAT = '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(funcName)s %(message)s'
LOG_LEVEL = logging.DEBUG if os.environ.get('DEBUG', '') else logging.INFO
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
