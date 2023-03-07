import segmentation_models_pytorch as smp
import torch
import numpy as np


class Model:
    def __init__(self):
        self.model = smp.Unet(classes=1, decoder_attention_type="scse")

        path = "ml_backend/model_epoch059_loss0.pt"
        self.model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
        self.model.to("cpu")
        self.model.eval()

    def predict_proba(self, model_input: torch.Tensor) -> np.ndarray:
        """
        Predict mask
        Note: Input must be 224*224
        :param torch.Tensor model_input: model input
        :return np.ndarray: Predicted
        """
        with torch.inference_mode():
            return self.model(model_input).detach().cpu().numpy().squeeze()

