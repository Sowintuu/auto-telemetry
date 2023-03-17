import logging
import warnings


class LogTelemetry(logging):

    def __init__(self):
        logging.__init__(self)

    def warning(self, text):
        logging.warning(text)
        warnings.warn(text)

    def info(self, text):
        logging.info(text)
        print(text)



