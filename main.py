import logging
import os
import threading
import time
from neonize.utils import log

from luna import Runner
from luna.config import BOT_NAME, DIR_COMMANDS

log.setLevel(logging.CRITICAL)


# Intervally clear tmp folder
def clear_tmp_folder():
    while True:
        time.sleep(60 * 60 * 24)  # 24 hours
        for file in os.listdir("tmp"):
            try:
                os.remove(f"tmp/{file}")
            except Exception as e:
                print(e)


try:
    clear_tmp_folder_thread = threading.Thread(target=clear_tmp_folder)
    clear_tmp_folder_thread.start()
except KeyboardInterrupt:
    pass


def main():
    bot = Runner(BOT_NAME, dir_commands=DIR_COMMANDS)
    bot.run()


if __name__ == "__main__":
    main()
