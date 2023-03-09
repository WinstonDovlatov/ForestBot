import queue
import time
from ml_backend.model import Model
import ml_backend.utils
from PIL import Image
from pathlib import Path
import cv2
import numpy as np


class Artifact:
    def __init__(self, chat_id, img_name):
        self.chat_id = chat_id
        self.img_name = img_name


class Controller:
    request_queue = queue.Queue()

    def __init__(self, callback):
        self.callback = callback
        self.model = Model()

    def observe_updates(self):
        while True:
            if not Controller.request_queue.empty():
                self.__analyse_image()
            time.sleep(0.1)

    def __analyse_image(self):
        current = Controller.request_queue.get()
        raw_input = np.asarray(Image.open(Path(f"input_photos/{current.img_name}")).convert("RGB"))

        model_input = ml_backend.utils.preprocess(raw_input)
        prediction = self.model.predict_proba_with_crop(model_input)
        result = ml_backend.utils.postprocess(raw_input, prediction)

        result_path = Path(f"result_photos/{current.img_name}").with_suffix(".jpg")
        cv2.imwrite(str(result_path), result)

        self.callback(result_path, current.chat_id)
