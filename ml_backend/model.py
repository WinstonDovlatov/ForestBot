import segmentation_models_pytorch as smp
import numpy as np
from ml_backend.utils import resize_to_model_input
from pathlib import Path
from tqdm import tqdm
import onnxruntime


class Model:
    def __init__(self, input_size):
        self.model = smp.Unet(classes=1, decoder_attention_type="scse")
        model_path = Path('processes/model.onnx')
        self.model = onnxruntime.InferenceSession(str(model_path))
        self.input_name = self.model.get_inputs()[0].name
        self.input_size = input_size

    @staticmethod
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    def predict_proba_crop(self, input: np.ndarray, crop_size: int) -> np.ndarray:
        lines = []
        for i in tqdm(np.arange(input.shape[0] // crop_size)):
            line = []
            for j in np.arange(input.shape[1] // crop_size):
                crop = input[
                       i * crop_size:(i + 1) * crop_size,
                       j * crop_size:(j + 1) * crop_size
                       ]
                crop = resize_to_model_input(crop, self.input_size)
                model_input = np.expand_dims(np.array(crop).transpose(2, 0, 1), axis=0)
                model_output = np.array(self.model.run(None, {self.input_name: model_input})).squeeze()
                line.append(model_output)
            lines.append(line)

        result = Model.sigmoid(np.block(lines))
        return result

    def predict_proba(self, input: np.ndarray) -> np.ndarray:
        # TODO: я это не тестил
        """
        Predict with resized image to model input size
        :param np.ndarray input: preprocessed image
        :return np.ndarray: prediction result
        """
        model_input = np.expand_dims(np.array(input).transpose(2, 0, 1), axis=0)
        model_output = np.array(self.model.run(None, {self.input_name: model_input})).squeeze()
        return Model.sigmoid(model_output)
