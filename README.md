# camtrap

## Traitement des données issues de pièges photo/vidéo

https://github.com/microsoft/CameraTraps/blob/master/megadetector.md

```
python3.9 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install tensorflow pillow humanfriendly matplotlib tqdm jsonpickle statistics requests python-dotenv
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

# dump d'une image

Le dump est une option de videoDetect2Json

python bin/videoDetect2Json.py -p 30 -l 240 -d -r /home/vprunet/Vidéos /home/vprunet/Vidéos/Maille\ 6/2020-05-14/IMG_0095.MP4

## annotate_image

Construit une image annotée à partir d'un rapport de détection (produit par videoDetect2Json.py) et d'une image (obtenue avec l'option dump de videoDetect2Json.json).
TODO : normaliser les arguments et construire à la volée les images sources.

```
python bin/annotate_image.py --help
python bin/annotate_image.py -i data/frames data/detection/.../report.json output_directory
```

python bin/annotate_image.py -i data/frames data/detection/frames/Maille\ 6/2020-05-14/IMG_0095.MP4-0.json foo

python bin/annotate_image.py -i data/frames data/detection/frames/Maille\ 6/2020-05-14/IMG_0095.MP4-240.json foo

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

# Exiftool

Monter le disque de médias et extraire les métadonnées brutes avec exiftool.

```
cd media_root_directory
exiftool -fast -json -groupNames --printConv --composite -ext mp4 -textOut "/home/vprunet/src/PNM/camtrap/data/exif/%d%F.json" -recurse Maille\ *
```

Attention, les fichiers json déjà présents ne sont pas recalculés. S'ils sont corrompus, ils doivent être supprimés avant d'exécuter exiftool.

Un fichier est produit pour chaque média.

# Metadata

Les métadonnées sont calculées à partir des données exif.
Exécuter

`python bin/metadata.py`

pour construire les fichiers de métadonnées (qui seront déposés dans le répertoire data/metadata)

Un fichier est construit pour chaque visite.
Les fichiers calculés écrasent les fichiers préexistants.
Effacer à la main (ou au préalable) les fichiers correspondant à des visites supprimées ou renommées.

# Megadetector

python /home/vprunet/src/PNM/camtrap/bin/runMegadetector.py -r /media/vprunet/INTENSO/ -p 300 -c "[0, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1200]" /media/vprunet/INTENSO/

exécute Megadetector sur les médias en argument.

Actuellement, l'algorithme n'utilise pas les métadonnées (cela pourrait changer, par exemple pour grouper les médias avant d'exécuter Megadetector).

Un fichier est produit pour chaque image traitée.

Les fichiers sont écrits dans le répertoire data/detection/frames

# Megadetector Data

python dashboard/megadetectorData.py

reconstruit la synthèse de megadetector pour chaque media source.

Les fichiers sont écrits dans le répertoire data/detection/megadetector

# Dashboard

```

pip install dash, dash-auth
pip install pandas
pip install -U scikit-image
pip install python-dotenv
pip install dash-bootstrap-components
python bin/dashboard.py

```

Enregistrer les préférences (MEDIA_ROOT, ...) dans .env à la racine du projet.

Lancer le serveur dash
python dashboard/camtrap.py

# Divers

video player
https://community.plotly.com/t/how-to-use-html-video/37529
https://community.plotly.com/t/adding-video-player/5303
