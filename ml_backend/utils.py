import numpy as np
import cv2
import torchvision
import torch


def preprocess(image: np.ndarray):
    with torch.inference_mode():
        to_tensor = torchvision.transforms.ToTensor()
        image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_NEAREST)
        image = to_tensor((image.astype(np.float32) / 255.0)).unsqueeze(0)
        image = image.to("cpu")
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
