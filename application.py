from forest_bot import ForestBot
import os
import time


def start_bot():
    try:
        forest_bot = ForestBot()
        forest_bot.start()
    except Exception as e:
        print(f"Failed to run bot. Restarting with 3 seconds delay...\n{e}")
        time.sleep(3)
        start_bot()
    else:
        print("!!!Bot is working!!!")


if __name__ == "__main__":
    if not os.path.exists("input_photos"):
        os.makedirs("input_photos")

    if not os.path.exists("result_photos"):
        os.makedirs("result_photos")

    start_bot()
