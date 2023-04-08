import torch
import segmentation_models_pytorch as smp
import onnxruntime
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")
torch_model_path = Path('model_epoch059_loss0.pt')
onnx_model_path = Path('model.onnx')
model_input_shape = (1, 3, 224, 224)

if __name__ == "__main__":
    to_np = np.array
    to_tensor = torch.Tensor
    sample_input = np.random.rand(*model_input_shape).astype(np.float32)

    torch_model = smp.Unet(classes=1, decoder_attention_type="scse")
    torch_model.load_state_dict(torch.load(torch_model_path, map_location=torch.device('cpu')))
    torch_model.to("cpu")
    torch_model.eval()

    torch.onnx.export(torch_model, to_tensor(sample_input), onnx_model_path)
    onnx_model = onnxruntime.InferenceSession(str(onnx_model_path))

    onnx_input_name = onnx_model.get_inputs()[0].name

    pred_onnx = to_np(onnx_model.run(None, {onnx_input_name: sample_input})).squeeze()
    pred_torch = torch_model(to_tensor(sample_input)).detach().cpu().numpy().squeeze()

    assert np.array_equal(pred_onnx.shape, pred_torch.shape), "shape mismatch"
    assert np.allclose(pred_onnx, pred_torch), "predictions are different"

    print(f"All tests passed. Model is correct.\nSaved in {onnx_model_path}")


