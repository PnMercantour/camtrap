# camtrap

## Traitement des données issues de pièges photo/vidéo

Le projet camtrap a été conçu et développé au Parc national du Mercantour pour faciliter le traitement en masse des médias (photos et vidéos) issus de pièges photo.

Le projet comprend une application interactive et des modules de traitement automatique des médias.

Les modules de traitement ont pour rôle d'analyser automatiquement les médias et d'en extraire des caractéristiques exploitées ensuite par l'application interactive.

L'application interactive est une web app qui permet sur un seul écran de consulter les médias (photos et vidéos), annotés et/ou filtrés à partir des résultats des modules de traitement, de saisir des observations relatives à ces médias, de visualiser sous différentes formes (observations par espèce, rapports) les données enregistrées par l'outil.

L'application permet le traitement rapide de nombreux médias. Plusieurs utilisateurs peuvent l'utiliser simultanément et partager leurs résultats en temps réel.

Deux modules de traitement sont opérationnels, le module exif [exiftool](https://exiftool.org/) qui extrait les métadonnées des médias (date précise, durée) et le module [megadetector](https://github.com/microsoft/CameraTraps/blob/master/megadetector.md) qui détecte automatiquement les médias d'intérêt en reconnaissant par une technique IA de deep learning la présence de faune sauvage, d'humains et de véhicules sur les médias.

D'autres modules, en particulier des modules de classification automatique d'espèces, seront prochainement intégrés dans l'environnement.

## Installation

Le projet a été testé sur linux (debian et ubuntu) et macos. Il n'a pas été testé sur windows.

Pour une installation simple, cloner le projet depuis github sur votre serveur.

Pour une installation distribuée (web app et modules de traitement sur des serveurs distincts), cloner le projet sur chacun des deux serveurs.

Puis procéder aux étapes d'installation de l'application et des modules de traitement.

### Application interactive

Nécessite python 3.7 ou ultérieure (python 3.9 si installation conjointe du module megadetector).

```
python3.x -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install python-dotenv
pip install dash, dash-auth, dash-bootstrap-components
pip install pandas
```

### Module exif

Installer [exiftool](https://exiftool.org/).

https://exiftool.org/install.html#Unix

### Module megadetector

[megadetector](https://github.com/microsoft/CameraTraps/blob/master/megadetector.md) est un composant IA de détection de faune dans des images, construit sur le moteur de deep learning [tensorflow](https://www.tensorflow.org/).

#### Installation de megadetector

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

Exporter la variable d'environnement MEGADETECTOR qui sera exploitée par les scripts du projet.

```
export MEGADETECTOR=<...>/microsoft/md_v4.1.0.pb
```

### Installation des dépendances du module megadetector

Nécessite python 3.9 ou ultérieure (peut être adapté si nécessaire pour accepter python 3.7 en jouant sur l'utilisation de argparse).

```
python3.9 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install tensorflow pillow humanfriendly matplotlib tqdm jsonpickle statistics requests python-dotenv
```

Installer également opencv

https://pypi.org/project/opencv-python/

```
pip install opencv-python
```

#### Vérification de l'installation de megadetector

Lancer un script microsoft sur une vidéo de test.

```
python <...>/microsoft/cameratraps/detection/process_video.py --debug_max_frames 60 <...>/microsoft/md_v4.1.0.pb test/mon_image.MP4

python <...>/microsoft/cameratraps/detection/process_video.py --debug_max_frames 30 --output_video_file foo.mp4 --render_output_video True <...>/microsoft/md_v4.1.0.pb test/mon_image.MP4
```

ou lancer le script PNM `runMegadetector`.

    python megadetector/runMegadetector.py --help

Des messages doivent indiquer que le moteur de deep learning tensorflow est correctement installé (et si un GPU a été trouvé sur le serveur).

Un GPU n'est pas nécessaire au fonctionnement du module. Par contre, l'utilisation d'un GPU compatible est recommandée pour accélérer les traitements sur les gros projets (d'un facteur 10 dans notre configuration où le temps de traitement d'une image est descendu de 5s à 0,4s).

La compatibilité de tensorflow avec les OS/GPU et les procédures d'installation détaillées des bibliothèques nécessaires évoluant rapidement, se référer à la documentation de [tensorflow](https://www.tensorflow.org/) et des fabricants pour l'installation du support GPU sur un serveur.

## Utilisation

### Organisation des médias

Organisation hiérarchique des fichiers dans une arborescence site/visite/media

### Exiftool

Exiftool permet d'extraire les métadonnées des média dans des fichiers json. Un fichier est produit pour chaque média dans le répertoire data/exif

```
cd <media_root_directory>
exiftool -fast -json -groupNames --printConv --composite -ext mp4 -textOut "<camtrap_project_root>/data/exif/%d%F.json" -recurse *
```

Attention, les fichiers json déjà présents ne sont pas recalculés. S'ils sont corrompus, ils doivent être supprimés avant d'exécuter exiftool.

### Metadata

Les métadonnées brutes produites par exiftool sont mises en forme au format de l'application

    python dashboard/metadata.py

Les fichiers de métadonnées produits sont déposés dans le répertoire data/metadata
Un fichier est construit pour chaque visite.
Les fichiers calculés écrasent les fichiers préexistants.
Effacer à la main (ou au préalable) les fichiers correspondant à des visites supprimées ou renommées.

### Megadetector

Le script python runMegadetector.py inspecte récursivement les répertoires et les fichiers donnés en paramètre et construit des rapports de détection au format json.

    usage: runMegadetector.py [-h] [-f FIRST_FRAME] [-l LAST_FRAME] [-p PICK] [-c CUSTOM] [--overwrite | --no-overwrite] [-d | --dump | --no-dump] [--detector_file DETECTOR_FILE] [-r ROOT]
                            [-o OUTPUT] [-i IMAGE_OUTPUT]
                            media [media ...]

    Batch processing of media files with megadetector.

    positional arguments:
      media                 source media folder or file

    optional arguments:
      -h, --help            show this help message and exit
      -f FIRST_FRAME, --first_frame FIRST_FRAME
                            first frame
      -l LAST_FRAME, --last_frame LAST_FRAME
                            last frame
      -p PICK, --pick PICK  pick every nth frame
      -c CUSTOM, --custom CUSTOM
                            custom frame list
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

Par exemple:

    python megadetector/runMegadetector.py -r <media_root_dir> -p 300 -c "[0, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1200]" <media subdir or file to process>

Un fichier est produit pour chaque image traitée, suivant le format `<chemin_source>[-<frame>].json`

Les fichiers sont écrits dans le répertoire data/detection/frames.
Cette opération est de loin la plus coûteuse en temps de calcul (de l'ordre de 0,5 à 5 secondes par image traitée), ce qui explique qu'on conserve les données non agrégées.

### Megadetector Data

le script megadetectorData.py agrège les données de détection pour les besoins de l'application interactive.

    python dashboard/megadetectorData.py

reconstruit la synthèse de megadetector pour chaque media source.

Les fichiers produits sont écrits dans le répertoire data/detection/megadetector

### Dashboard

```
?? pip install -U scikit-image
```

Enregistrer les préférences (MEDIA_ROOT, ...) dans .env à la racine du projet.

Lancer le serveur dash
python dashboard/camtrap.py

## Divers

## video player dans l'application interactive

https://community.plotly.com/t/how-to-use-html-video/37529
https://community.plotly.com/t/adding-video-player/5303

## videoMetadata

Enregistre les métadonnées lues directement avec opencv dans les fichiers source vidéo.
Ce programme n'est **pas** compatible avec la chaîne de traitement.

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

## annotate_image

Copie à peine modifiée d'un script microsoft (utilisé teporairement pour analyser le résultat du megadetector en attendant mieux).

Construit une image annotée à partir d'un rapport de détection (produit par videoDetect2Json.py) et d'une image (obtenue avec l'option dump de videoDetect2Json.json).
TODO : normaliser les arguments et construire à la volée les images sources.

```
python bin/annotate_image.py --help
python bin/annotate_image.py -i data/frames data/detection/.../report.json output_directory
```

python bin/annotate_image.py -i data/frames data/detection/frames/Maille\ 6/2020-05-14/IMG_0095.MP4-0.json foo

python bin/annotate_image.py -i data/frames data/detection/frames/Maille\ 6/2020-05-14/IMG_0095.MP4-240.json foo

## showFrame

Le script showFrame extrait des frames d'une vidéo source et les affiche et/ou les enregistre.

La visualisation d'images est une version modifiée de visualize_detector_output.

- répertoire des vidéos
- numéro de frame
- chargement en mémoire de la frame
- traitement (bounding boxes, etc)
- écriture dans un répertoire de sortie ou tmp
- affichage
