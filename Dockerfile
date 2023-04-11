FROM python:3.8-slim
ENV CONDA_DIR /opt/conda

RUN mkdir -p /usr/src/workdir
WORKDIR /usr/scr/workdir

RUN apt update && apt install -y libhdf4-dev && apt install -y libgeos-dev && apt install -y curl && \
apt install ffmpeg libsm6 libxext6  -y && apt install -y wget && rm -rf /var/lib/apt/lists/*

RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-424.0.0-linux-arm.tar.gz
RUN tar -xf google-cloud-cli-424.0.0-linux-arm.tar.gz && \
rm google-cloud-cli-424.0.0-linux-arm.tar.gz

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
/bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

RUN pip install torch~=1.13.1 torchvision~=0.14.1 --index-url https://download.pytorch.org/whl/cpu
RUN conda install -c conda-forge geos

COPY forestbot ./forestbot
COPY entrypoint.py generate_credentials.py requirements.txt ./

RUN pip install -r requirements.txt

RUN sed -i '/from nbdev.imports import test_eq/d' /opt/conda/lib/python3.10/site-packages/banet/core.py

RUN gdwon 1TB5jgmAtDGfUffj9J9SUg8K5AZc7prFk && mv model.onnx forestbot/processes/model.onnx

CMD ["bash"]
