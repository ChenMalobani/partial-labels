
# because tensorflow.keras.applications doesn't have ResNet101 for some reason we have this workaround
# ONLY works with keras_applications=1.0.7 since 1.0.6 doesn't have ResNet101 an 1.0.8 removed the set_keras_submodules function
import tensorflow

import keras_applications
keras_applications.set_keras_submodules(
    backend=tensorflow.keras.backend,
    layers=tensorflow.keras.layers,
    models=tensorflow.keras.models,
    utils=tensorflow.keras.utils
)

from tensorflow.keras import Model, Input
# from tensorflow.keras.applications import ResNet101, ResNet50

from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import RMSprop, Adam

from model.losses import BCE
from model.metrics import MAP
from model.networks import BaseModel

from model.utils.config import cfg


class Baseline(BaseModel):

    def build(self):
        self.build_classifier()

        inp = Input(shape=self.input_shape, name='image_input')

        # classifier
        x = self.cls_model(inp)

        # dense + sigmoid for multilabel classification
        x = Flatten()(x)
        output = Dense(self.n_classes, activation='sigmoid')(x)

        self.model = Model(inputs=inp, outputs=output)
        self.log('Outputs shape %s' % str(self.model.output_shape))

        optimizer = self.build_optimizer()
        loss = BCE()
        self.model.compile(loss=loss, optimizer=optimizer)

        if self.verbose:
            self.log('Final model summary')
            self.model.summary()

    def build_classifier(self):
        cls_model = keras_applications.resnet.ResNet101(include_top=False, weights='imagenet', input_shape=self.input_shape)
        self.cls_model = Model(inputs=cls_model.inputs, outputs=cls_model.output, name='cls_model')

        if self.verbose:
            self.log('Classifier model')
            self.cls_model.summary()

    def build_optimizer(self):
        '''
        TODO: something better than an ugly switch <3
        '''
        if cfg.TRAINING.OPTIMIZER == 'rmsprop':
            return RMSprop(lr=cfg.TRAINING.START_LR)
        elif cfg.TRAINING.OPTIMIZER == 'adam':
            return Adam(lr=cfg.TRAINING.START_LR)
        raise Exception('Unknown optimizer %s' % cfg.TRAINING.OPTIMIZER)
