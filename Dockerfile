FROM tensorflow/tensorflow:1.12.0-gpu
WORKDIR /model
COPY source /model
RUN pip install -r requirements.txt

