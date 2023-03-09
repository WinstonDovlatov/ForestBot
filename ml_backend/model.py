import segmentation_models_pytorch as smp
import torch
import numpy as np
import torchvision
from tqdm import tqdm


class Model:
    def __init__(self):
        self.model = smp.Unet(classes=1, decoder_attention_type="scse")

        path = "ml_backend/model_epoch059_loss0.pt"
        self.model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
        self.model.to("cpu")
        self.model.eval()

    def predict_proba_with_crop(self, input: np.ndarray):
        to_tensor = torchvision.transforms.ToTensor()
        lines = []
        for i in tqdm(np.arange(input.shape[0] // 224)):
            line = []
            for j in np.arange(input.shape[1] // 224):
                crop = input[i * 224:(i + 1) * 224, j * 224:(j + 1) * 224]
                with torch.inference_mode():
                    model_input = to_tensor(crop).unsqueeze(0).to('cpu')
                    model_output = self.model(model_input).detach().cpu().numpy().squeeze()
                line.append(model_output)
            lines.append(line)

        result = np.block(lines)
        return result

    def predict_proba(self, model_input: torch.Tensor) -> np.ndarray:
        """
        Predict mask
        Note: Input must be 224*224
        :param torch.Tensor model_input: model input
        :return np.ndarray: Predicted
        """
        with torch.inference_mode():
            return self.model(model_input).detach().cpu().numpy().squeeze()
