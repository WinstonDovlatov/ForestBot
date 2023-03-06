from forest_bot import ForestBot
import torch
import cv2
import segmentation_models_pytorch
from PIL import Image
import numpy as np
import os
import time

import matplotlib.pyplot as plt

# path = "ML_backend/model_epoch059_loss0.pt"
# model = segmentation_models_pytorch.Unet(classes=1, decoder_attention_type="scse")
# model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
# model.eval()
#
#
# #image = Image.open('ML_backend/example.jpg')
#
# image = np.asarray(Image.open('ML_backend/example.jpg'))
#
# image = cv2.resize(image, (224, 224), interpolation=cv2.INTER_NEAREST)
#
# image = image.reshape(3, 224, 224)
#
# image = torch.Tensor(image.astype(np.float32) / 255.0).unsqueeze(0)
#
# mask = model(image).detach().squeeze(0).numpy().reshape(224, 224, 1)
#
# threshold = -1
# mask[mask >= threshold] = 1
# mask[mask < threshold] = 0
#
# cv2.imshow("result", mask)
# cv2.waitKey(0)


# model.eval()
# model.predict(image)

def start_bot():
    try:
        forest_bot = ForestBot()
        forest_bot.start()
    except Exception as e:
        print(f"Failed to run bot. Restarting with 3 seconds delay...\n{e}")
        time.sleep(3)
        start_bot()
    else:
        print("!!!Bot is working!!!")


if __name__ == "__main__":
    if not os.path.exists("input_photos"):
        os.makedirs("input_photos")

    if not os.path.exists("result_photos"):
        os.makedirs("result_photos")

    start_bot()
