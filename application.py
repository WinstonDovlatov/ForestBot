from forest_bot_front.forest_bot import ForestBot
import os
import time


def start_bot() -> None:
    try:
        forest_bot = ForestBot()
        forest_bot.start()
    except Exception as e:
        print(f"Failed to run bot. Restarting with 3 seconds delay...\n{e}")
        time.sleep(3)
        start_bot()
    else:
        print("!!!Bot is working again!!!")


if __name__ == "__main__":
    required_folders = ['input_photos', 'result_photos', 'osm']
    for folder in required_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    start_bot()
