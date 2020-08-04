"""
Python logging.Handler which writes log messages to the macro output

Example::

    import logging

    from sardana.macroserver.macro import macro

    logger = logging.getLogger("bl99")


    @macro()
    def do_stuff(self):
        with MacroOutputLogHandler(self, logger=logger):
           ...
           logger.info("started doing stuff")
           ...
"""

import logging


class MacroOutputLogHandler(logging.Handler):

    def __init__(self, macro, logger=logging.root, level=logging.NOTSET):
        super().__init__(level)
        self.macro = macro
        self.logger = logger
        self.level = level

    def __enter__(self):
        self.logger.addHandler(self)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.logger.removeHandler(self)

    def emit(self, record):
        self.macro.output(self.format(record))

