# Utilitaires

## exiftool

```
exiftool -fast -json -groupNames  --printConv --composite -ext mp4 -textOut "data/exiftool/%:3d%f.%e.json" -recurse /mnt/f/Maille\ 6/

exiftool -csv --printconv -sourcefile -filesize -filetype -createdate -duration -sourceimagewidth -sourceimageheight -compressorID -videoframerate /mnt/f/Maille\ 6/2020-03-11/IMG_0001.MP4

exifSummary
exiftool -csv -fileOrder createDate --printconv -sourcefile -createdate -duration Maille\ 6/2020-03-11/ >data/exifDigest/Maille\ 6/2020-03-11.csv

```

`%:3d` a pour effet de supprimer /mnt/f à l'écriture des fichiers.
Les fichiers json référencent le chemin complet du fichier source.

## recherche de véhicules

grep -lr "\"3\"" data/detection/frames/Maille\ 70/2020-08-27/ |sort
