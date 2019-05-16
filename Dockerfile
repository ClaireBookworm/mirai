FROM tensorflow/tensorflow:1.12.0-gpu
WORKDIR /model
COPY source /model

ADD https://s3-us-west-2.amazonaws.com/deepai-object-detection-experiments/interns/claire/mri/model_weights/meta_mask_rcnn_mri-1200images-4plus-inner_iter-40-3050-4-620.h5 weights.h5

RUN pip install -r requirements.txt
