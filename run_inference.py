import os
import sys
import numpy as np
import skimage

# Root directory of the project
ROOT_DIR = os.path.abspath(".")

# Import Mask RCNN
sys.path.append(ROOT_DIR)  # To find local version of the library
from config import Config
import utils
#import mrcnn.model as modellib

import matterport_mask_rcnn as modellib
from matterport_mask_rcnn import load_image_gt


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
    DETECTION_MIN_CONFIDENCE = 0.95
    
inference_config = InferenceConfig()

class_names = ['BG', "Tumor", "Empty1", "Empty2",
                    "Empty3", "Empty4"]


inference_config = InferenceConfig()


model_path = ''

def process(original_image, model_path, inference_config, class_names, polygon=True):
    model = modellib.MaskRCNN(mode="inference", 
                                  config=inference_config,
                                  model_dir=model_path)

    # Load trained weights
    #print("Loading weights from ", model_path)
    model.load_weights(model_path, by_name=True)

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
    return rois, masks, class_ids, scores