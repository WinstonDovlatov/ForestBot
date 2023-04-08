from threading import Timer
import os
import time
from pathlib import Path


class Cleaner:
    periodicity = 10 * 60
    time_threshold = 25 * 60
    shift_in_name = 100000

    def __init__(self, target_dirs):
        self.target_dirs = target_dirs

    def start(self):
        Timer(interval=Cleaner.periodicity, function=self.__clean).start()

    def __clean(self):
        print("cleaning started at", round(time.time() * 100000))
        for target_dir in self.target_dirs:
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    try:
                        file_time = int(file.split('&')[-1][5:].split('.')[0])
                        delta = (time.time() * Cleaner.shift_in_name - file_time) / Cleaner.shift_in_name
                        if delta > Cleaner.time_threshold:
                            print(delta)
                            os.remove(Path(root) / Path(file))
                            print(Path(root) / Path(file), "deleted")
                    except Exception as e:
                        print(e)

        Timer(interval=Cleaner.periodicity, function=self.__clean).start()
