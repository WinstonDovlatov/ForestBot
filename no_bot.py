# Данный файл предоставляет возможность тестировать модель без использования бота


from ml_backend.controller import Controller, Artifact
from threading import Thread
import os
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import imutils

model_input_size = 224
use_crop = True
crop_size = 224
photo_name = "example1.png"  # must be in input_photos folder


def callback(*args, **kwargs):
    res_path = Path(f"result_photos/{photo_name}".split('.')[0]).with_suffix('.jpg')
    print(f"result saved in:\n{res_path}")
    res = np.asarray(Image.open(res_path).convert("RGB"))
    res = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
    res = imutils.resize(res, width=1000)
    cv2.imshow("result", res)
    cv2.waitKey(0)


def predict(source: str) -> None:
    controller = Controller(
        callback=callback,
        model_input_size=model_input_size,
        use_crop=use_crop,
        crop_size=crop_size if use_crop else None
    )
    print("Started...")

    Thread(target=controller.observe_updates).start()
    controller.request_queue.put(Artifact(228, source))


if __name__ == "__main__":
    if not os.path.exists("input_photos"):
        os.makedirs("input_photos")

    if not os.path.exists("result_photos"):
        os.makedirs("result_photos")

    predict(photo_name)
