# camtrap

Traitement des données issues de pièges photo/vidéo

https://github.com/microsoft/CameraTraps/blob/master/megadetector.md

python3.9 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install tensorflow pillow humanfriendly matplotlib tqdm jsonpickle statistics requests

Utilisation de megadetector
Créer un répertoire microsoft
cloner les repos suivants:
git clone https://github.com/Microsoft/cameratraps -b tf1-compat
git clone https://github.com/Microsoft/ai4eutils
télécharger le modèle megadetector pour tensorflow
https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb
export PYTHONPATH=/Users/vincent/src/microsoft/cameratraps:/Users/vincent/src/microsoft/ai4eutils

opencv
https://pypi.org/project/opencv-python/
pip install opencv-python

ln -s /Users/vincent/src/microsoft/cameratraps/detection/run_tf_detector bin/
ln -s /Users/vincent/src/microsoft/cameratraps/detection/run_tf_detector_batch.py bin/

python /Users/vincent/src/microsoft/cameratraps/detection/process_video.py --debug_max_frames 60 ../../microsoft/md_v4.1.0.pb ../../pieges_photo/Test\ Data/Stephane/2020-07-27/IMG_0006.MP4

--output_video_file
--render_output_video True
--n_cores 2

python /Users/vincent/src/microsoft/cameratraps/detection/process_video.py --debug_max_frames 30 --output_video_file foo.mp4 --render_output_video True --n_cores 2 ../../microsoft/md_v4.1.0.pb img/IMG_0006.MP4

/Users/vincent/src/PNM/camtrap/.venv/bin/python /Users/vincent/src/PNM/camtrap/bin/parseTest.py img/IMG_0006.MP4 -d frames -l 1000 -p 30

sur PC
2020-08-24
python bin/videoDetector.py -d frames  -p 30 /mnt/d/camtrap/2020-08-24/IMG_0015.MP4 
15 vide
16 chamois
17 chamois nocturne
18 invalide