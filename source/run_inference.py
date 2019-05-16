import io
import os
import sys
import numpy as np
import skimage
from PIL import  Image
# Root directory of the project
ROOT_DIR = os.path.abspath(".")

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from config import Config
import utils
#import mrcnn.model as modellib

import mask_rcnn as modellib
from mask_rcnn import load_image_gt

from scipy.misc import imsave

import tensorflow as tf
from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
config.gpu_options.per_process_gpu_memory_fraction = 0.2
sess = tf.Session(config=config)
set_session(sess)  # set this TensorFlow session as the default session for Keras

def apply_mask(image, mask, color, alpha=0.5):
    """Apply the given mask to the image.
    """
    """
    for c in range(3):
        image[:, :, c] = np.where(mask == 1,
                                  image[:, :, c] *
                                  (1 - alpha) + alpha * color[c] * 255,
                                  image[:, :, c])
    """
    mask = mask[:,:,0]*255*alpha
    image[:,:,0] = image[:,:,0]*(1.0-alpha) + mask*alpha
    return image


def make_masked_image(image, boxes, masks, class_ids, class_names,
                      scores=None, title="",
                      figsize=(16, 16), ax=None,
                      show_mask=True, 
                      colors=None, ):
    """
    boxes: [num_instance, (y1, x1, y2, x2, class_id)] in image coordinates.
    masks: [height, width, num_instances]
    class_ids: [num_instances]
    class_names: list of class names of the dataset
    scores: (optional) confidence scores for each box

    """
    # Number of instances
    try:
        N =  len(masks)
    except:
        print("\n*** No instances to display *** \n")


    masked_image = image.astype(np.uint32).copy()
    for i in range(N):
        color = [1,0,0]
        if class_ids[i] == 1:
            mask = np.array(masks[i])
            print mask.shape
            if show_mask:
               masked_image = apply_mask(masked_image, mask, color)

    return masked_image
  
def load_image(image, config, augment=False, augmentation=None,
                  use_mini_mask=False, debug=False):
    """Load and return ground truth data for an image (image, mask, bounding boxes).
    augment: (deprecated. Use augmentation instead). If true, apply random
        image augmentation. Currently, only horizontal flipping is offered.
    augmentation: Optional. An imgaug (https://github.com/aleju/imgaug) augmentation.
        For example, passing imgaug.augmenters.Fliplr(0.5) flips images
        right/left 50% of the time.
    use_mini_mask: If False, returns full-size masks that are the same height
        and width as the original image. These can be big, for example
        1024x1024x100 (for 100 instances). Mini masks are smaller, typically,
        224x224 and are generated by extracting the bounding box of the
        object and resizing it to MINI_MASK_SHAPE.
    Returns:
    image: [height, width, 3]
    shape: the original shape of the image before resizing and cropping.
    class_ids: [instance_count] Integer class IDs
    bbox: [instance_count, (y1, x1, y2, x2)]
    mask: [height, width, instance_count]. The height and width are those
        of the image unless use_mini_mask is True, in which case they are
        defined in MINI_MASK_SHAPE.
    """
    # Load image and mask
    original_shape = image.shape

    image, window, scale, padding, crop = utils.resize_image(
        image,
        min_dim=config.IMAGE_MIN_DIM,
        min_scale=config.IMAGE_MIN_SCALE,
        max_dim=config.IMAGE_MAX_DIM,
        mode=config.IMAGE_RESIZE_MODE)

    return image

class InferenceConfig(Config):
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    DETECTION_MIN_CONFIDENCE = 0.5
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    BATCH_SIZE = 1
    NAME = 'test'
    # Number of classes (including background)
    NUM_CLASSES = 1 + 5 # background + 5 shapes

    # Use small images for faster training. Set the limits of the small side
    # the large side, and that determines the image shape.
    IMAGE_MIN_DIM = 4
    IMAGE_MAX_DIM = 1024

    # Use smaller anchors because our image and objects are small
    #RPN_ANCHOR_SCALES = (8, 16, 32, 64, 128)  # anchor side in pixels
    RPN_ANCHOR_SCALES = (12, 32, 80, 196, 480)
    
inference_config = InferenceConfig()

class_names = ['BG', "Tumor", "Empty1", "Empty2",
                    "Empty3", "Empty4"]


inference_config = InferenceConfig()


model_path = 'weights.h5'

def save_image_in_memory(image, data_format='channels_first'):
   if data_format == 'channels_first':
       image = np.transpose(image, [1, 2, 0])  # CHW --> HWC
   image *= 255
   image = np.clip(image, 0, 255)
   imgByteArr = io.BytesIO()
   imsave(imgByteArr, image.astype(np.uint8), 'JPEG')
   imgByteArr = imgByteArr.getvalue()
   return imgByteArr
  
def process(original_image, model_path, inference_config, class_names, polygon=False):
    model = modellib.MaskRCNN(mode="inference", 
                                  config=inference_config,
                                  model_dir='./')

    # Load trained weights
    #print("Loading weights from ", model_path)
    model.load_weights(model_path, by_name=True)
    
    original_image = Image.open(original_image).convert('RGB')
    original_image = load_image(np.array(original_image), inference_config)
    results = model.detect([original_image], verbose=1)

    r = results[0]
    rois = r['rois']
    masks = r['masks']
    class_ids = r['class_ids']

    scores = r['scores']
    """
    print 'num detections:', len(class_names)
    for k, score in zip(r['class_ids'], r['scores']):
        print k,dataset.class_names[k],':',score
    
    """
    resized_masks = []
    for i in range(r['masks'].shape[-1]):
        resized = np.array(utils.resize(r['masks'][:,:,i], original_image.shape), dtype=np.int)
        if polygon:
            resized = convert_mask_to_polygon(resized)
        resized_masks.append(resized)
    
    return rois, resized_masks, class_ids, scores, original_image
  
if __name__ == "__main__":
  test_image_path = 'test_images/test_1.jpg'
  model_path = 'weights.h5'
  class_names = ['BG', "Tumor", "Empty1", "Empty2",
                    "Empty3", "Empty4"]
  inference_config = InferenceConfig()
  rois, masks, class_ids, scores, original_image = process(
      original_image=test_image_path,
      model_path=model_path,
      inference_config=inference_config,
      class_names=class_names,
      polygon=False)
  print masks
  masked_image = make_masked_image(original_image, boxes=rois, masks=masks, class_ids=class_ids, class_names=class_names)
  image_string = save_image_in_memory(masked_image)
  open('/output/output.jpg', 'wb').write(image_string)
