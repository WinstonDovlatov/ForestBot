import queue
import time
from ml_backend.model import Model
import ml_backend.utils
from PIL import Image
from pathlib import Path
import cv2
import numpy as np
import warnings


class Artifact:
    def __init__(self, chat_id, img_name):
        self.chat_id = chat_id
        self.img_name = img_name


class Controller:
    default_crop_size = 400
    request_queue = queue.Queue()

    def __init__(self, callback, model_input_size, use_crop=True, crop_size=None):
        self.callback = callback
        self.model_input_size = model_input_size
        self.use_crop = use_crop
        self.crop_size = crop_size
        if use_crop and crop_size is None:
            self.crop_size = Controller.default_crop_size
            warnings.warn(f"Selected cropping, but crop_size is not provided. "
                          f"Use default value: {Controller.default_crop_size}")

        if not use_crop and crop_size is not None:
            warnings.warn(f"Selected no cropping, but crop_size is provided. "
                          f"It will have no effect")

        self.model = Model(input_size=self.model_input_size)

    def observe_updates(self) -> None:
        """Check if there are new images for prediction"""
        while True:
            if not Controller.request_queue.empty():
                self.__analyse_image()
            time.sleep(0.1)

    def __analyse_image(self) -> None:
        """Do all prediction work and notify bot about finish using callback"""
        current = Controller.request_queue.get()
        raw_input = np.asarray(Image.open(Path(f"input_photos/{current.img_name}")).convert("RGB"))
        model_input = ml_backend.utils.preprocess(raw_input)

        if self.use_crop:
            model_input = ml_backend.utils.resize_for_cropping(model_input, self.crop_size)
            prediction = self.model.predict_proba_crop(model_input, crop_size=self.crop_size)

        else:
            model_input = ml_backend.utils.resize_to_model_input(model_input, self.crop_size)
            prediction = self.model.predict_proba(model_input)

        result = ml_backend.utils.postprocess(raw_input, prediction)

        result_path = Path(f"result_photos/{current.img_name}").with_suffix(".jpg")
        cv2.imwrite(str(result_path), result)

        self.callback(result_path, current.chat_id)
