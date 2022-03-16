Mise aux normes du premier disque 8To

(.venv) vprunet@cgpia:~/src/PNM/camtrap$ ls -R /media/vprunet/INTENSO/ |grep .MP4 |wc -l
96724
(.venv) vprunet@cgpia:~/src/PNM/camtrap$ ls -R /media/vprunet/INTENSO/ |grep .JPG |wc -l
59880

run megadetector sur la maille 6, 2 premières secondes des fichier MP4.
python bin/videoDetect2Json.py -p 30 -l 120 -r /media/vprunet/INTENSO/ /media/vprunet/INTENSO/Maille 6

secondes 3, 4, 5.
python bin/videoDetect2Json.py -p 60 -f 180 -l 300 -r /media/vprunet/INTENSO/ /media/vprunet/INTENSO/Maille 6

/home/vprunet/src/PNM/camtrap/.venv/bin/python /home/vprunet/src/PNM/camtrap/bin/runMegadetector.py -r /media/vprunet/INTENSO/ -p 300 -c "[0, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1200]" /media/vprunet/INTENSO/

---

synchro entre deux disques 8To

rsync -a -n -i -v /media/vprunet/INTENSO/Maille\ 100 /media/vprunet/INTENSO1
-a pour archive
-n pour dry-run
-i pour le détail des opérations
-v pour verbose

visite 53 2020-07-03
la vraie date de visite était probablement 2020-07-05. On garde 2020-07-03, c'est sans incidence.

Sauvegarde des données camtrap
rsync -a /home/vprunet/src/PNM/camtrap/data /media/vprunet/LaCie/

exiftool -fast -json -groupNames --printConv --composite -ext mp4 -textOut "/home/vprunet/src/PNM/camtrap/data/exif/%d%F.json" -recurse Maille\ \*

python dashboard/metadata.py

python dashboard/megadetectorData.py
