
https://www.tensorflow.org/install/gpu

docker run -it tensorflow /bin/bash

https://www.tensorflow.org/install?hl=fr

https://www.tensorflow.org/api_docs/python/tf?hl=fr

images docker tensorflow
https://hub.docker.com/r/tensorflow/tensorflow/

essai du container tensorflow jupyter
docker run -it --rm --gpus all tensorflow/tensorflow:latest-gpu-jupyter /bin/bash

import tensorflow as tf
tf.config.list_physical_devices()
# https://www.tensorflow.org/api_docs/python/tf/config/list_physical_devices?hl=fr

>>> tf.config.list_physical_devices()
[PhysicalDevice(name='/physical_device:CPU:0', device_type='CPU'), PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
>>> tf.config.list_logical_devices()
[LogicalDevice(name='/device:CPU:0', device_type='CPU'), LogicalDevice(name='/device:GPU:0', device_type='GPU')]

docker run -u $(id -u):$(id -g) -v /home/vprunet/src:/src -v /home/vprunet/Vidéos:/Vidéos -w /src/PNM/camtrap -it --rm --gpus all tensorflow/tensorflow:latest-gpu-jupyter /bin/bash
