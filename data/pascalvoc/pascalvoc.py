'''
http://host.robots.ox.ac.uk/pascal/VOC/voc2007/index.html#devkit
'''
import math
import os

from collections import defaultict

import numpy as np
from PIL import Image

from data import Dataset
from data.pascalvoc.preprocessing import utils

from model.utils.config import cfg


class PascalVOC(Dataset):

    supported_keys = ('image', 'multilabel')

    def __init__(self,
                 dataset_path,
                 mode,
                 x_keys,
                 y_keys):
        '''
        Only multilabel for now
        dataset_path is the folder where VOCdevkit/VOC2007/ is contained

        Note: shuffle is managed in the fit_generator, not at all here
        '''
        assert mode in ['train', 'val', 'trainval', 'test'], 'Unknown mode %s' % str(mode)

        self.dataset_path = dataset_path
        self.mode = mode
        self.x_keys = x_keys
        self.y_keys = y_keys
        self.all_keys = set(x_keys + y_keys)
        assert all([k in self.supported_keys for k in self.all_keys]), 'Unexpected key in %s' % str(self.all_keys)

        self.batch_size = cfg.BATCH_SIZE

        self.class_info = utils.load_ids()
        self.n_classes = len(self.class_info)

        self.samples = defaultict(dict)
        self.load_annotations(os.path.join(dataset_path, 'VOCdevkit/VOC2007/Annotations/annotations_multilabel_%s.csv' % mode))

        Dataset.__init__(self)

    def __len__(self):
        '''
        Should give off the number of batches
        '''
        return math.floor(self.n_samples / self.batch_size)

    def load_annotations(self, annotations_path):
        '''
        for now we only load the multilabel classification annotations.

        example line :
        000131,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-1,0,-1,-1,-1,-1,-1
        '''

        samples = defaultict(dict)

        # multilabel annotations
        with open(annotations_path, 'r') as f_in:
            for line in f_in:
                parts = line.strip().split(',')
                ground_truth = [int(val) for val in parts[1:]]
                assert all([gt in [-1, 0, 1] for gt in ground_truth])
                samples[parts[0]]['multilabel'] = ground_truth

        # we sort it by # sample to make sure it's always the same order
        self.sample_ids = sorted(samples.keys())
        self.samples = {k: samples[k] for k in self.sample_ids}
        self.n_samples = len(self.samples)

    def __getitem__(self, batch_idx):
        '''
        required by the Sequence api
        return a batch, composed of x_batch and y_batch
        TODO: data augmentation should take place here
        '''
        batch_data = self._load_data(batch_idx)

        # Convert the dictionary of samples to a list for x and y
        x_batch = []
        for key in self.x_keys:
            x_batch.append(batch_data[key])

        y_batch = []
        for key in self.y_keys:
            y_batch.append(batch_data[key])

        return x_batch, y_batch

    def _load_data(self, batch_idx):
        '''
        Used by Dataset.__getitem__ during batching
        '''
        data_dict = {}
        for key in self.all_keys:
            data_dict[key] = np.empty((self.batch_size,) + self.get_key_shape(key))

        for i in range(self.batch_size):
            sample_idx = batch_idx * self.batch_size + i
            if sample_idx >= self.n_samples:
                sample_idx -= self.n_samples

            data = self.get_data_dict(sample_idx)
            for key in self.allkeys:
                data_dict[key][i, :] = data[key]

        return data_dict

    def get_data_dict(self, sample_idx):
        output = {}
        sample_id = self.sample_ids[sample_idx]

        output['frame'] = self.get_image(sample_id)
        output['multilabel'] = self.samples[sample_id]['multilabel']

        return output

    def get_image(self, img_id):
        '''
        open the image with given id (like 000131)
        TODO: we want it to fail if an image is not found, but we should make it fail gracefully
        '''
        image_path = os.path.join(self.dataset_path, 'VOCdevkit/VOC2007/JPEGImages/%s.jpg' % img_id)
        return Image.open(image_path)
