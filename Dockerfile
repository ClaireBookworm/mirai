FROM tensorflow/tensorflow:1.12.0-gpu
WORKDIR /model

RUN apt update && apt install -y wget python-tk

COPY source/requirements.txt .
RUN pip install -r requirements.txt
RUN wget https://s3-us-west-2.amazonaws.com/deepai-object-detection-experiments/interns/claire/mri/model_weights/meta_mask_rcnn_mri-1200images-4plus-inner_iter-40-3050-4-620.h5 -O weights.h5

COPY source /model
COPY test_images test_images

CMD []
ENTRYPOINT ["python", "run_inference.py"]
