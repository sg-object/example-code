from tempfile import TemporaryDirectory

from datumaro.components.dataset import Dataset
from cvat.apps.dataset_manager.bindings import (GetCVATDataExtractor,
    import_dm_annotations, match_dm_item, find_dataset_root)
from cvat.apps.dataset_manager.util import make_zip_archive
from datumaro.components.extractor import DatasetItem

from .transformations import RotatedBoxesToPolygons
from .registry import dm_env, exporter, importer

import shutil
from os.path import exists, join, relpath
from os import mkdir, listdir
from glob import glob
from PIL import Image
from pathlib import Path
import json

from pyunpack import Archive
import ast
from datumaro.plugins.yolo_format.extractor import YoloExtractor

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

subset_train = 'Train'
subset_valid = 'Validation'
subset_test = 'Test'

@exporter(name='YOLO', ext='ZIP', version='5.0')
def _export(dst_file, instance_data, save_images=False):
    instance_name = 'project' if 'project' in instance_data.meta.keys() else 'task'
    labels = [label for _, label in instance_data.meta[instance_name]['labels']]
    label_names = [label['name'] for label in labels]
    
    label_dict = {}
    for idx, item in enumerate(label_names):
      label_dict[item] = str(idx)
    
    train_image_dict = {}
    valid_image_dict = {}
    test_image_dict = {}
    for frame_data in instance_data.group_by_frame():
      name = frame_data.name
      index = name.rfind('.')
      if index > 0:
        name = name[:index]
      
      info = {
        'width': frame_data.width,
        'height': frame_data.height
      }

      if hasattr(frame_data, 'subset'):
        subset = frame_data.subset
        if subset == subset_train:
          train_image_dict[name] = info
        elif subset == subset_valid:
          valid_image_dict[name] = info
        else:
          test_image_dict[name] = info
      else:
        train_image_dict[name] = info

    dataset = Dataset.from_extractors(GetCVATDataExtractor(instance_data,
        include_images=save_images), env=dm_env)

    with TemporaryDirectory() as tmp_dir:
        dataset.transform(RotatedBoxesToPolygons)
        dataset.transform('polygons_to_masks')
        dataset.transform('merge_instance_segments')
        dataset.export(tmp_dir, format='kitti', save_images=save_images)

        with TemporaryDirectory() as yolo_dir:
            __createDataYaml(yolo_dir, label_names)

            kitti_default_path = tmp_dir + '/default/'
            if exists(kitti_default_path):
              __convertSubset(kitti_default_path, yolo_dir + '/train/', label_dict, train_image_dict)
            else:
              kitti_train_path = tmp_dir + '/' + subset_train + '/'
              if exists(kitti_train_path):
                __convertSubset(kitti_train_path, yolo_dir + '/train/', label_dict, train_image_dict)

              kitti_valid_path = tmp_dir + '/' + subset_valid + '/'
              if exists(kitti_valid_path):
                __convertSubset(kitti_valid_path, yolo_dir + '/valid/', label_dict, valid_image_dict)

              kitti_test_path = tmp_dir + '/' + subset_test + '/'
              if exists(kitti_test_path):
                __convertSubset(kitti_test_path, yolo_dir + '/test/', label_dict, test_image_dict)
            
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


obj_train_dir = 'obj_train_data'
train_txt = 'train.txt'
obj_data_format = """classes = {0}
names = data/obj.names
backup = backup/
"""
@importer(name='YOLO', ext='ZIP', version='5.0')
def _import(src_file, instance_data, load_data_callback=None):
  with TemporaryDirectory() as src_dir:
    Archive(src_file.name).extractall(src_dir)
    with TemporaryDirectory() as dst_dir:
      nc = []
      names = []
      with open(join(src_dir, 'data.yaml')) as file:
        for line in file.readlines():
          if line.startswith('nc'):
            nc = line.split(':', 1)
          elif line.startswith('names'):
            names = line.split(':', 1)
  
      if len(nc) < 2:
        raise Exception('')
      elif len(names) < 2:
        raise Exception('')
      
      classes = int(nc[1])
      name_arr = ast.literal_eval(names[1].strip())
      obj_data = obj_data_format.format(classes)

      src_train_path = join(src_dir, 'train')
      if exists(src_train_path):
        dst_train_path = join(dst_dir, obj_train_dir)
        mkdir(dst_train_path)
        obj_data += 'train = data/{0}\n'.format(train_txt)
        src_label_path = join(src_train_path, yolo_label_dir)
        if exists(src_label_path):
          for label in listdir(src_label_path):
            shutil.move(join(src_label_path, label), dst_train_path)
        src_image_path = join(src_train_path, yolo_image_dir)
        if exists(src_image_path):
          with open(join(dst_dir, train_txt), 'w') as file:
            for image in listdir(src_image_path):
              shutil.move(join(src_image_path, image), dst_train_path)
              file.write(join('data', obj_train_dir, image) + '\n')

              label_file_path = join(dst_train_path, image[:image.rfind('.')] + '.txt')
              if not exists(label_file_path):
                tmp_file = open(label_file_path, 'w')
                tmp_file.close()

      with open(join(dst_dir, 'obj.data'), 'w') as file:
        print(obj_data, file=file)

      with open(join(dst_dir, 'obj.names'), 'w') as file:
        for name in name_arr:
          file.write(name + '\n')

      frame_names = []
      image_info = {}
      frames = [YoloExtractor.name_from_path(relpath(p, dst_dir))
        for p in glob(join(dst_dir, '**', '*.txt'), recursive=True)]
      root_hint = find_dataset_root(
        [DatasetItem(id=frame) for frame in frames], instance_data)
      for frame in frames:
        frame_info = None
        try:
          frame_id = match_dm_item(DatasetItem(id=frame), instance_data,
            root_hint=root_hint)
          frame_info = instance_data.frame_info[frame_id]
        except Exception: # nosec
          pass
        if frame_info is not None:
          image_info[frame] = (frame_info['height'], frame_info['width'])
          frame_names.append(frame_info['path'])
      
      train_txt_path = join(dst_dir, train_txt)
      if not exists(train_txt_path):
        with open(train_txt_path, 'w') as file:
          for name in frame_names:
            file.write(join('data', obj_train_dir, name) + '\n')

      dataset = Dataset.import_from(dst_dir, 'yolo',
        env=dm_env, image_info=image_info)
      if load_data_callback is not None:
        load_data_callback(dataset, instance_data)
      import_dm_annotations(dataset, instance_data)
