FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/src/test_docker
WORKDIR /usr/scr/test_docker
COPY . .

RUN apt update && apt install -y libhdf4-dev && apt install -y libgeos-dev && apt-get install -y curl
RUN apt-get install ffmpeg libsm6 libxext6  -y

RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-424.0.0-linux-arm.tar.gz
RUN tar -xf google-cloud-cli-424.0.0-linux-arm.tar.gz

RUN conda install -c conda-forge geos

RUN pip install -r requirements.txt

RUN sed -i '9d' /opt/conda/lib/python3.10/site-packages/banet/core.py

CMD ["bash"]