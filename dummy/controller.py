import queue
import time
from dummy.model import Model
from dummy.utils import Postprocessor, Preprocessor
from PIL import Image
from pathlib import Path
import asyncio


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
        raw_input = Image.open(Path(f"input_photos/{current.img_name}")).convert("RGB")
        model_input = Preprocessor.preprocess(raw_input)
        prediction = self.model.predict_proba(model_input)

        result = Postprocessor.postprocess(raw_input, prediction)

        # TODO: схуяли .bmp не отправляется
        # сохраняем все в .жопэгэ
        # no_bmp_name = current.img_name.split('.')[0] + '.jpg'
        result_path = Path(f"result_photos/{current.img_name}").with_suffix(".jpg")
        result.save(result_path)
        ####
        ####
        time.sleep(1)
        ####
        ####
        self.callback(result_path, current.chat_id)
