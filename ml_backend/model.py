import segmentation_models_pytorch as smp
import torch
import numpy as np
import torchvision
from ml_backend.utils import resize_to_model_input
import time
from tqdm import tqdm


class Model:
    def __init__(self, input_size):
        self.model = smp.Unet(classes=1, decoder_attention_type="scse")
        path = "ml_backend/model_epoch059_loss0.pt"
        self.model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
        self.model.to("cpu")
        self.model.eval()
        self.input_size = input_size

    def predict_proba_crop(self, input: np.ndarray, crop_size: int) -> np.ndarray:
        """
        Predict with cropping
        :param np.ndarray input: preprocessed image
        :param int crop_size: size of each crop
        :return np.ndarray: prediction result
        """
        start = time.time()
        to_tensor = torchvision.transforms.ToTensor()
        crops = []
        for i in np.arange(input.shape[0] // crop_size):
            for j in np.arange(input.shape[1] // crop_size):
                crop = input[
                       i * crop_size:(i + 1) * crop_size,
                       j * crop_size:(j + 1) * crop_size]
                crop = resize_to_model_input(crop, self.input_size)
                crops.append(to_tensor(crop).unsqueeze(0).to('cpu'))
        with torch.inference_mode():
            batch = torch.cat(crops)
            results = self.model(batch).detach().cpu().numpy().squeeze()

        line_length = input.shape[1] // crop_size
        lines = []
        for i in np.arange(input.shape[0] // crop_size):
            lines.append(np.hstack(results[i * line_length: (i + 1) * line_length]))
        result = np.vstack(lines)

        print(f"{time.time() - start:.2f}")
        return result

    def predict_proba(self, input: np.ndarray) -> np.ndarray:
        """
        Predict with resized image to model input size
        :param np.ndarray input: preprocessed image
        :return np.ndarray: prediction result
        """
        with torch.inference_mode():
            to_tensor = torchvision.transforms.ToTensor()
            model_input = to_tensor(input).unsqueeze(0).to('cpu')
            result = self.model(model_input).detach().cpu().numpy().squeeze()
            return result
