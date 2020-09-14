# MIT License
#
# Copyright (C) The Adversarial Robustness Toolbox (ART) Authors 2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import numpy as np
import pytest
import torch
import torch.nn as nn

from art.estimators.classification.pytorch import PyTorchClassifier
from art.defences.preprocessor.spatial_smoothing import SpatialSmoothing
from art.defences.preprocessor.spatial_smoothing_pytorch import SpatialSmoothingPyTorch
from art.attacks.evasion import FastGradientMethod

from tests.attacks.utils import backend_test_defended_images


@pytest.fixture()
def fix_get_mnist_subset(get_mnist_dataset):
    (x_train_mnist, y_train_mnist), (x_test_mnist, y_test_mnist) = get_mnist_dataset
    n_train = 100
    n_test = 11
    yield x_train_mnist[:n_train], y_train_mnist[:n_train], x_test_mnist[:n_test], y_test_mnist[:n_test]


# A generic test for various preprocessing_defences, forward pass.
def _test_preprocessing_defences_forward(
    get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
):
    (_, _), (x_test_mnist, y_test_mnist) = get_default_mnist_subset

    classifier_, _ = image_dl_estimator()

    clip_values = (0, 1)
    criterion = nn.CrossEntropyLoss()
    classifier = PyTorchClassifier(
        clip_values=clip_values,
        model=classifier_.model,
        preprocessing_defences=preprocessing_defences,
        loss=criterion,
        input_shape=(1, 28, 28),
        nb_classes=10,
        device_type=device_type,
    )

    with torch.no_grad():
        predictions_classifier = classifier.predict(x_test_mnist)

    # Apply the same defences by hand
    x_test_defense = x_test_mnist
    for defence in preprocessing_defences:
        x_test_defense, _ = defence(x_test_defense, y_test_mnist)

    x_test_defense = torch.tensor(x_test_defense)
    with torch.no_grad():
        predictions_check = classifier_.model(x_test_defense)
    predictions_check = predictions_check.cpu().numpy()

    # Check that the prediction results match
    np.testing.assert_array_almost_equal(predictions_classifier, predictions_check, decimal=4)


# A generic test for various preprocessing_defences, backward pass.
def _test_preprocessing_defences_backward(
    get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
):
    (_, _), (x_test_mnist, y_test_mnist) = get_default_mnist_subset

    classifier_, _ = image_dl_estimator()

    clip_values = (0, 1)
    criterion = nn.CrossEntropyLoss()
    classifier = PyTorchClassifier(
        clip_values=clip_values,
        model=classifier_.model,
        preprocessing_defences=preprocessing_defences,
        loss=criterion,
        input_shape=(1, 28, 28),
        nb_classes=10,
        device_type=device_type,
    )

    # The efficient defence-chaining.
    pseudo_gradients = np.random.randn(*x_test_mnist.shape)
    gradients_in_chain = classifier._apply_preprocessing_defences_gradient(x_test_mnist, pseudo_gradients)

    # Apply the same backward pass one by one.
    x = x_test_mnist
    x_intermediates = [x]
    for defence in classifier.preprocessing_defences[:-1]:
        x = defence(x)[0]
        x_intermediates.append(x)

    gradients = pseudo_gradients
    for defence, x in zip(classifier.preprocessing_defences[::-1], x_intermediates[::-1]):
        gradients = defence.estimate_gradient(x, gradients)

    np.testing.assert_array_almost_equal(gradients_in_chain, gradients, decimal=4)


@pytest.mark.only_with_platform("pytorch")
@pytest.mark.parametrize("device_type", ["cpu", "gpu"])
def test_nodefence(get_default_mnist_subset, image_dl_estimator, device_type):
    preprocessing_defences = []
    _test_preprocessing_defences_forward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )
    _test_preprocessing_defences_backward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )


@pytest.mark.only_with_platform("pytorch")
@pytest.mark.parametrize("device_type", ["cpu", "gpu"])
def test_defence_pytorch(get_default_mnist_subset, image_dl_estimator, device_type):
    smooth_3x3 = SpatialSmoothingPyTorch(window_size=3, channels_first=True, device_type=device_type)
    preprocessing_defences = [smooth_3x3]
    _test_preprocessing_defences_forward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )
    _test_preprocessing_defences_backward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )


@pytest.mark.only_with_platform("pytorch")
@pytest.mark.parametrize("device_type", ["cpu", "gpu"])
def test_defence_non_pytorch(get_default_mnist_subset, image_dl_estimator, device_type):
    smooth_3x3 = SpatialSmoothing(window_size=3, channels_first=True)
    preprocessing_defences = [smooth_3x3]
    _test_preprocessing_defences_forward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )
    _test_preprocessing_defences_backward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )


@pytest.mark.xfail(reason="Preprocessing-defence chaining only supports defences implemented in PyTorch.")
@pytest.mark.only_with_platform("pytorch")
@pytest.mark.parametrize("device_type", ["cpu", "gpu"])
def test_defences_pytorch_and_nonpytorch(get_default_mnist_subset, image_dl_estimator, device_type):
    smooth_3x3_nonpth = SpatialSmoothing(window_size=3, channels_first=True)
    smooth_3x3_pth = SpatialSmoothingPyTorch(window_size=3, channels_first=True, device_type=device_type)
    preprocessing_defences = [smooth_3x3_nonpth, smooth_3x3_pth]
    _test_preprocessing_defences_forward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )
    _test_preprocessing_defences_backward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )


@pytest.mark.only_with_platform("pytorch")
@pytest.mark.parametrize("device_type", ["cpu", "gpu"])
def test_defences_chaining(get_default_mnist_subset, image_dl_estimator, device_type):
    smooth_3x3 = SpatialSmoothingPyTorch(window_size=3, channels_first=True, device_type=device_type)
    smooth_5x5 = SpatialSmoothingPyTorch(window_size=5, channels_first=True, device_type=device_type)
    smooth_7x7 = SpatialSmoothingPyTorch(window_size=7, channels_first=True, device_type=device_type)
    preprocessing_defences = [smooth_3x3, smooth_5x5, smooth_7x7]
    _test_preprocessing_defences_forward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )
    _test_preprocessing_defences_backward(
        get_default_mnist_subset, image_dl_estimator, device_type, preprocessing_defences
    )


@pytest.mark.only_with_platform("pytorch")
@pytest.mark.parametrize("device_type", ["cpu", "gpu"])
def test_fgsm_defences(fix_get_mnist_subset, image_dl_estimator, device_type):

    clip_values = (0, 1)
    smooth_3x3 = SpatialSmoothingPyTorch(window_size=3, channels_first=True, device_type=device_type)
    smooth_5x5 = SpatialSmoothingPyTorch(window_size=5, channels_first=True, device_type=device_type)
    smooth_7x7 = SpatialSmoothingPyTorch(window_size=7, channels_first=True, device_type=device_type)
    classifier_, _ = image_dl_estimator()

    criterion = nn.CrossEntropyLoss()
    classifier = PyTorchClassifier(
        clip_values=clip_values,
        model=classifier_.model,
        preprocessing_defences=[smooth_3x3, smooth_5x5, smooth_7x7],
        loss=criterion,
        input_shape=(1, 28, 28),
        nb_classes=10,
        device_type=device_type,
    )
    assert len(classifier.preprocessing_defences) == 3

    attack = FastGradientMethod(classifier, eps=1, batch_size=128)
    backend_test_defended_images(attack, fix_get_mnist_subset)
