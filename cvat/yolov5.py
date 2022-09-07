from tempfile import TemporaryDirectory

from datumaro.components.dataset import Dataset
from cvat.apps.dataset_manager.bindings import (GetCVATDataExtractor)
from cvat.apps.dataset_manager.util import make_zip_archive

from .transformations import RotatedBoxesToPolygons
from .registry import dm_env, exporter

import shutil
from os.path import exists
from os import mkdir, listdir
import glob
from PIL import Image
from pathlib import Path
import json

########################################

yaml_format = """train: ../train/images
val: .../valid/images

nc: {0}
names: {1}"""

def __createDataYaml(dir_path, class_list):
  data = yaml_format.format(len(class_list), class_list)
  with open(dir_path + '/data.yaml', 'w') as file:
    print(data, file=file)

########################################

def __createContent(line, label_dict, width, height):
  arr = line.split(' ', 8)
  label = arr[0]
  xmin = float(arr[4])
  ymin = float(arr[5])
  xmax = float(arr[6])
  ymax = float(arr[7])

  dw = 1. /width
  dh = 1. / height

  x = (xmin + xmax) / 2.0
  y = (ymin + ymax) / 2.0

  w = xmax - xmin
  h = ymax - ymin

  x = x * dw
  w = w * dw
  y = y * dh
  h = h * dh
  return ' '.join([label_dict[label], str(round(x, 6)), str(round(y, 6)), str(round(w, 6)), str(round(h, 6))])

####################################################

kitti_image_dir = 'image_2'
kitti_label_dir = 'label_2'

yolo_image_dir = 'images'
yolo_label_dir = 'labels'

#def __getImageSize(kitti_image_path, file):
#  file_name = file[:file.rfind('.')]
#  img_list = glob.glob(kitti_image_path + '/{0}.*'.format(file_name))
#  for img_path in img_list:
#    img_name = Path(img_path).stem
#    if file_name == img_name:
#      image = Image.open(img_path)
#      width, height = image.size
#      return width, height

def __convertSubset(kitti_subset_path, yolo_subset_path, label_dict, image_dict):
  mkdir(yolo_subset_path)

  kitti_label_path = kitti_subset_path + kitti_label_dir
  if exists(kitti_label_path):
    yolo_label_path = yolo_subset_path + yolo_label_dir
    mkdir(yolo_label_path)
    file_list = listdir(kitti_label_path)
    for file in file_list:
      file_name = file[:file.rfind('.')]
      image = image_dict[file_name]
      content = []
      with open(kitti_label_path + '/' + file) as origin_file:
        for line in origin_file:
          content.append(__createContent(line, label_dict, image['width'], image['height']))
      with open(yolo_label_path + '/' + file, 'w') as new_file:
        for line in content:
          new_file.write(line)
          new_file.write('\n')

  kitti_image_path = kitti_subset_path + kitti_image_dir
  if exists(kitti_image_path):
    shutil.move(kitti_image_path, yolo_subset_path + yolo_image_dir)

#######################################################

@exporter(name='YOLO', ext='ZIP', version='5.0')
def _export(dst_file, instance_data, save_images=False):
    instance_name = 'project' if 'project' in instance_data.meta.keys() else 'task'
    labels = [label for _, label in instance_data.meta[instance_name]['labels']]
    label_names = [label['name'] for label in labels]
    
    label_dict = {}
    for idx, item in enumerate(label_names):
      label_dict[item] = str(idx)
    
    image_dict = {}
    for frame_data in instance_data.group_by_frame():
      name = frame_data.name
      index = name.rfind('.')
      if index > 0:
        name = name[:index]
      image_dict[name] = {
        'width': frame_data.width,
        'height': frame_data.height
      }

    dataset = Dataset.from_extractors(GetCVATDataExtractor(instance_data,
        include_images=save_images), env=dm_env)

    with TemporaryDirectory() as tmp_dir:
        dataset.transform(RotatedBoxesToPolygons)
        dataset.transform('polygons_to_masks')
        dataset.transform('merge_instance_segments')
        dataset.export(tmp_dir, format='kitti', save_images=save_images)

        with TemporaryDirectory() as yolo_dir:
            __createDataYaml(yolo_dir, label_names)

            kitti_train_path = tmp_dir + '/Train/'
            if exists(kitti_train_path):
                __convertSubset(kitti_train_path, yolo_dir + '/train/', label_dict, image_dict)

            kitti_valid_path = tmp_dir + '/Validation/'
            if exists(kitti_valid_path):
                __convertSubset(kitti_valid_path, yolo_dir + '/valid/', label_dict, image_dict)

            kitti_test_path = tmp_dir + '/Test/'
            if exists(kitti_test_path):
                __convertSubset(kitti_test_path, yolo_dir + '/test/', label_dict, image_dict)
            
            make_zip_archive(yolo_dir, dst_file)
            
        def test():
            with open(yolo_dir + '/' + 'yolo.txt', 'w') as file:
                for i in listdir(tmp_dir):
                    file.write(i)
                    file.write('\n')
                file.write('==============================')
                file.write('\n')
                print(label_names, file=file)
                file.write('\n')
                for idx, item in enumerate(label_names):
                  label_dict[item] = idx
                  file.write(str(idx) + ' : ' + item)
                  file.write('\n')
                file.write('==============================')
                file.write('\n')
                print(label_dict, file=file)
                print(instance_data, file=file)
            make_zip_archive(yolo_dir, dst_file)

