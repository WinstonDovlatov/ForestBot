FROM python:3.8.16
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /usr/src/test_docker
WORKDIR /usr/scr/test_docker

COPY . .

RUN apt update
RUN apt install -y libhdf4-dev
RUN apt install -y libgeos-dev

RUN pip install -r requirements.txt

RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-424.0.0-linux-arm.tar.gz
RUN tar -xf google-cloud-cli-424.0.0-linux-arm.tar.gz


CMD ["bash"]