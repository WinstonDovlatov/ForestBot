import numpy as np
import cv2


def align(size: int, target_size: int) -> int:
    """
    Bring the number to target_size * n
    :param int target_size: value by which result should be divided by
    :param int size: original number
    :return int: closest target_size * n number to original
    """
    if size < target_size:
        return target_size

    if size % target_size < target_size / 2:
        return (size // target_size) * target_size
    else:
        return (size // target_size + 1) * target_size


def preprocess(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image before passing into the model, bring numbers to (0, 1)
    :param np.ndarray image: input image converted to np
    :return np.ndarray: preprocessed image
    """
    image = image.astype(np.float32) / 255.0
    return image


def resize_for_cropping(image: np.ndarray, crop_size: int) -> np.ndarray:
    """
    Make image size suit for cropping
    :param np.ndarray image: input image
    :param crop_size: size of each crop
    :return np.ndarray: resized image
    """
    image = cv2.resize(
        image,
        (align(image.shape[0], target_size=crop_size), align(image.shape[1], target_size=crop_size)),
        interpolation=cv2.INTER_NEAREST
    )
    return image


def resize_to_model_input(image: np.ndarray, model_input_size: int) -> np.ndarray:
    """Resize to model input size"""
    image = cv2.resize(image, (model_input_size, model_input_size), interpolation=cv2.INTER_NEAREST)
    return image


def postprocess(original_img: np.ndarray, prediction: np.ndarray, threshold: float) -> np.ndarray:
    """
    Postprocess prediction. Apply threshold, bring to original shape and combine with original image
    :param np.ndarray original_img: original image
    :param np.ndarray prediction: model prediction
    :param float threshold: threshold for prediction
    :return np.ndarray: combined prediction and image
    """
    cool_color_bgr = [235, 56, 226]

    prediction[prediction < threshold] = 0
    prediction[prediction >= threshold] = 1
    prediction = (prediction * 255).astype("uint8")

    roads = cv2.cvtColor(prediction, cv2.COLOR_GRAY2BGR)
    roads[np.where((roads == [255, 255, 255]).all(axis=2))] = cool_color_bgr
    roads = cv2.resize(roads, original_img.shape[0:2][::-1], interpolation=cv2.INTER_NEAREST)

    result = cv2.add(roads, cv2.cvtColor(original_img, cv2.COLOR_RGB2BGR))

    return result
