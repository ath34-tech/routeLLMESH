import logging
import sys


def setup_logger(level: str = "INFO") -> None:
    root_logger = logging.getLogger()

    root_logger.setLevel(level)

    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)


logger = logging.getLogger("RouteLM")