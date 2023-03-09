import numpy as np
from path import Path
from PIL import Image
from ml_backend.model import Model
import ml_backend.utils
import cv2


def predict(source: str, destination: str) -> None:
    """
    Prediction with crop without using TelegramBot
    :param source: path to source img
    :param destination: path to save result
    """
    raw_input = np.asarray(Image.open(Path(source)).convert("RGB"))
    model_input = ml_backend.utils.preprocess(raw_input)
    model = Model()

    prediction = model.predict_proba_with_crop(model_input)

    result = ml_backend.utils.postprocess(raw_input, prediction)

    cv2.imwrite(str(destination), result)


if __name__ == "__main__":
    source_img_path = r"C:\Users\James_Kok\PycharmProjects\ForestBot\input_photos\input_image&id=447178684&time=1678364483460.png"
    destination_path = "res.jpg"  # must be .jpg
    predict(source_img_path, destination_path)
    print("\n\n!!!DONE!!!")
