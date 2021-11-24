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

Ajouter les bibliothèques cameratraps et ai4eutils au path python.

```
export PYTHONPATH=<...>/microsoft/cameratraps:<...>/microsoft/ai4eutils
```

Télécharger le modèle megadetector pour tensorflow
https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb

Exporter la variable d'environnement MEGADETECTOR qui est exploitée par les scripts PNM.

```
export MEGADETECTOR=<...>/microsoft/md_v4.1.0.pb
```

## opencv

https://pypi.org/project/opencv-python/

```
pip install opencv-python
```

## Exemple d'utilisation des scripts microsoft

```
python <...>/microsoft/cameratraps/detection/process_video.py --debug_max_frames 60 <...>/microsoft/md_v4.1.0.pb test/mon_image.MP4

python <...>/microsoft/cameratraps/detection/process_video.py --debug_max_frames 30 --output_video_file foo.mp4 --render_output_video True <...>/microsoft/md_v4.1.0.pb test/mon_image.MP4
```

## Scripts PNM


## videoMetadata

Enregistre les métadonnées des fichiers source vidéo

```
python bin/videoMetadata.py --help
usage: videoMetadata.py [-h] [--overwrite | --no-overwrite] [-r ROOT] [-o OUTPUT] video [video ...]

Batch processor to store video metadata.

positional arguments:
  video                 source video folder or file

optional arguments:
  -h, --help            show this help message and exit
  --overwrite, --no-overwrite
                        overwrite existing results (default: False)
  -r ROOT, --root ROOT  base directory for source files
  -o OUTPUT, --output OUTPUT
                        base directory for video metadata

python bin/videoMetadata.py --root /mnt/f "/mnt/f/Maille 6"
```

## videoDetect2Json

Inspecte récursivement les répertoires et les fichiers donnés en paramètre et construit des rapport de détection au format json.

```
python bin/videoDetect2Json.py --help
usage: videoDetect2Json.py [-h] [-f FIRST_FRAME] [-l LAST_FRAME] [-p PICK] [--overwrite | --no-overwrite]
                           [-d | --dump | --no-dump] [--detector_file DETECTOR_FILE] [-r ROOT] [-o OUTPUT]
                           [-i IMAGE_OUTPUT]
                           video [video ...]

Batch processor for video files. Runs megadetector on each file then stores results into json files

positional arguments:
  video                 source video folder or file

optional arguments:
  -h, --help            show this help message and exit
  -f FIRST_FRAME, --first_frame FIRST_FRAME
                        first frame
  -l LAST_FRAME, --last_frame LAST_FRAME
                        last frame
  -p PICK, --pick PICK  pick every nth frame
  --overwrite, --no-overwrite
                        overwrite existing results (default: False)
  -d, --dump, --no-dump
                        dump images (default: False)
  --detector_file DETECTOR_FILE
  -r ROOT, --root ROOT  base directory for source files
  -o OUTPUT, --output OUTPUT
                        base directory for detection reports
  -i IMAGE_OUTPUT, --image_output IMAGE_OUTPUT
                        base directory for dumped images

python bin/videoDetect2Json.py -p 30 -l 240 -r /mnt/f/ "/mnt/f/Maille 6"

```

## annotate_image

Construit une image annotée à partir d'un rapport de détection (produit par videoDetect2Json.py) et d'une image (obtenue avec l'option dump de videoDetect2Json.json).
TODO : normaliser les arguments et construire à la volée les images sources.

```
python bin/annotate_image.py --help
python bin/annotate_image.py -i data/frames data/detection/.../report.json output_directory
```

## jsonAnalyser

Analyse et synthétise les rapports de détection sur les images.

### Exemple

```
python bin/videoDetect2Json.py -d -r /Users/vincent/Pictures/ /Users/vincent/Pictures/videos_loups_LMD/
python bin/videoMetadata.py -r /Users/vincent/Pictures/ /Users/vincent/Pictures/videos_loups_LMD/
python bin/annotate_image.py -i data/frames/videos_loups_LMD/  data/detection/frames/videos_loups_LMD/2020-12-18_2\ loups_Couletta.mp4-1230.json foo
```

### Performances

Détection sur cgp-sig (PC Xeon, OS Windows 10 WSL ubuntu).

Données de la Maille 6.

1974 videos, 11801 images : environ 6 images par vidéo.
Durée du traitement : en moyenne 6,35s par image.

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
