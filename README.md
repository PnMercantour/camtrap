# camtrap

## Traitement des données issues de pièges photo/vidéo

https://github.com/microsoft/CameraTraps/blob/master/megadetector.md

```
python3.9 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install tensorflow pillow humanfriendly matplotlib tqdm jsonpickle statistics requests
```

## Utilisation de megadetector

Créer un répertoire microsoft pour recueillir les bibliothèques microsoft et le modèle tensorflow

Cloner les repos cameratraps et ai4eutils:

```
git clone https://github.com/Microsoft/cameratraps -b tf1-compat
git clone https://github.com/Microsoft/ai4eutils
```

Télécharger le modèle megadetector pour tensorflow
https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb

```
export PYTHONPATH=<...>/microsoft/cameratraps:<...>/microsoft/ai4eutils
```

## opencv

https://pypi.org/project/opencv-python/

```
pip install opencv-python
```

### Exemple d'utilisation des scripts microsoft

```
python <...>/microsoft/cameratraps/detection/process_video.py --debug_max_frames 60 <...>/microsoft/md_v4.1.0.pb test/mon_image.MP4

python <...>/microsoft/cameratraps/detection/process_video.py --debug_max_frames 30 --output_video_file foo.mp4 --render_output_video True <...>/microsoft/md_v4.1.0.pb test/mon_image.MP4
```

## Scripts PNM

Exporter la variable d'environnement MEGADETECTOR

```
export MEGADETECTOR=<...>/microsoft/md_v4.1.0.pb
```

## videoMetadata

Enregistre les métadonnées des fichiers source vidéo

```
python bin/videoMetadata --root data/video data/video
```

## videoDetect2Json

Inspecte récursivement les répertoires et les fichiers donnés en paramètre et construit des rapport de détection au format json.

```
python bin/videoDetect2Json.py --help
```

### Exemple

```
python bin/videoDetect2Json.py -l 240 -p 30 -r img img
```

### Performances

Détection sur cgp-sig (PC Xeon, OS Windows 10 WSL ubuntu).

Données de la Maille 6.

1974 videos, 11801 images : environ 6 images par vidéo.
Durée du traitement : en moyenne 6,35s par image.

## jsonAnalyser

Analyse et synthétise les rapports de détection sur les images.

## visualisation

### showFrame

Le script showFrame extrait des frames d'une vidéo source et les affiche et/ou les enregistre.

La visualisation d'images est une version modifiée de visualize_detector_output.

- répertoire des vidéos
- numéro de frame
- chargement en mémoire de la frame
- traitement (bounding boxes, etc)
- écriture dans un répertoire de sortie ou tmp
- affichage

## Test

```
python bin/videoDetect2Json.py data/video/test/IMG_0006.MP4
```

Utiliser l'option --dump pour générer des images correspondant aux trames sélectionnées.

```
python bin/videoDetect2Json.py --dump data/video/test/IMG_0006.MP4
python bin/annotate_image.py  -i data/frames/test data/detection/frames/test/IMG_0006.MP4-1814.json data/annotated_frames/test
```
