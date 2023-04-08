from forestbot.front.forest_bot import ForestBot
import os
import time
import traceback
from forestbot.front.cleaner import Cleaner

def start_bot() -> None:
    try:
        forest_bot = ForestBot()
        forest_bot.start()
    except Exception:
        print(f"Failed to run bot. Restarting with 3 seconds delay...\n{traceback.format_exc()}")
        time.sleep(3)
        start_bot()
    else:
        print("!!!Bot is working again!!!")


if __name__ == "__main__":
    required_folders = ['input_photos', 'result_photos', 'osm']
    for folder in required_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    Cleaner(target_dirs=required_folders).start()
    start_bot()
