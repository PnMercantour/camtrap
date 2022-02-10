# Utilitaires

## exiftool

### Installation

https://exiftool.org/install.html#Unix


```
exiftool -fast -json -groupNames  --printConv --composite -ext mp4 -textOut "data/exiftool/%:3d%f.%e.json" -recurse /mnt/f/Maille\ 6/

exiftool -csv --printconv -sourcefile -filesize -filetype -createdate -duration -sourceimagewidth -sourceimageheight -compressorID -videoframerate /mnt/f/Maille\ 6/2020-03-11/IMG_0001.MP4

exifSummary
exiftool -csv -fileOrder createDate --printconv -sourcefile -createdate -duration Maille\ 6/2020-03-11/ >data/exifDigest/Maille\ 6/2020-03-11.csv

```

`%:3d` a pour effet de supprimer /mnt/f à l'écriture des fichiers.
Les fichiers json référencent le chemin complet du fichier source.

```
cd /media/vprunet/LaCie
exiftool -fast -json -groupNames  --printConv --composite -ext mp4 -textOut "/home/vprunet/src/PNM/camtrap/data/exif/%d%F.json" -recurse Maille\ *
``̀
204 directories scanned
  150 directories created
45294 image files read
45294 output files created


Anomalies sur 101 102 116 117 119 23 39 69 72 qui contiennent des fichiers jpeg ou sont mal classées (le répertoire visite n'est pas une date valide)

Traitement des metadonnées depuis le répertoire source data/exif vers le répertoire data/metadata
## recherche de véhicules

grep -lr "\"3\"" data/detection/frames/Maille\ 70/2020-08-27/ |sort
