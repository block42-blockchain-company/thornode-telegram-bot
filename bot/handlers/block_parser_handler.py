import subprocess
from subprocess import Popen

from constants.globals import logger
from handlers.mongodb_handler import get_current_churn_cycle

block_parser = None


def start_block_parser():
    global block_parser
    logger.info("Setting up block parser")
    block_parser = Popen(['../binaries/tmClient'], stdout=subprocess.DEVNULL)


def stop_block_parser():
    print("Terminating block parser ...")
    block_parser.terminate()


def check_block_parser_health():
    if block_parser.poll() is not None:
        logger.error("Block parser is not running anymore.")
        # TODO Do something to resolve this situtation
    else:
        logger.info(f"Current blockheight: {get_current_churn_cycle()['block_height_end']}")
