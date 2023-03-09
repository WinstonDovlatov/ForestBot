import numpy as np
import cv2
import torchvision
import torch

model_input_size = 224


def align(size: int):
    if size < model_input_size:
        return model_input_size

    if size % model_input_size < model_input_size / 2:
        return (size // model_input_size) * model_input_size
    else:
        return (size // model_input_size + 1) * model_input_size


def preprocess(image: np.ndarray):
    image = cv2.resize(
        image,
        (align(image.shape[0]), align(image.shape[1])),
        interpolation=cv2.INTER_NEAREST
    )
    image = image.astype(np.float32) / 255.0
    return image


def postprocess(original_img: np.ndarray, prediction: np.ndarray) -> np.ndarray:
    threshold = 0.01
    cool_color_bgr = [235, 56, 226]

    prediction[prediction < threshold] = 0
    prediction[prediction >= threshold] = 1
    prediction = (prediction * 255).astype("uint8")

    roads = cv2.cvtColor(prediction, cv2.COLOR_GRAY2BGR)
    roads[np.where((roads == [255, 255, 255]).all(axis=2))] = cool_color_bgr
    roads = cv2.resize(roads, original_img.shape[0:2][::-1], interpolation=cv2.INTER_NEAREST)

    result = cv2.add(roads, cv2.cvtColor(original_img, cv2.COLOR_RGB2BGR))

    return result
