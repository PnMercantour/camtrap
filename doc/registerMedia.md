# registerMedia.py

Le script registerMedia.py a une double fonction:

- enregistrer les fichiers et metadonnées exif dans la base de données
- enregistrer une copie complète des métadonnées exif dans des fichiers (un par répertoire traité).

```
(venv) vprunet@cgpia:~/src/PNM/camtrap_23$ python bin/registerMedia.py --root /home/vprunet/camtrap/EPHE/ -p test

Project test
Media storage root: /home/vprunet/camtrap/test
Database: service=camtrap_23

Entering .
Entering Maille 117
Entering Maille 117/2021-07-09
Processing Maille 117/2021-07-09
Processing Maille 117
Processing .
```

Ce script parcourt la hiérarchie de fichiers source sans connaître ni interpréter la sémantique de l'organisation des fichiers (sites, senseurs, visites, etc). Ce rôle est dévolu aux scripts de post traitement (voir les fichiers post_import_xxx.sql dans le répertoire sql).

```
psql -f sql/post_import_test.sql
INSERT 0 1
INSERT 0 1
INSERT 0 1
UPDATE 108
```

Les médias peuvent alors être parcourus avec l'application camtrap.

Indiquer dans le .env la racine de l'arborescence des fichiers

```
MEDIA_ROOT=/home/vprunet/camtrap/test
```

Créer le fichier config/users.json au format `{<login>:<password>, ...}`

Lancer camtrap dans son venv.

```
(venv) vprunet@cgpia:~/src/PNM/camtrap_23$ /home/vprunet/src/PNM/camtrap_23/venv/bin/python /home/vprunet/src/PNM/camtrap_23/src/camtrap.py

camtrap dashboard
project root: /home/vprunet/src/PNM/camtrap_23
media root:/home/vprunet/camtrap/test
data root:/home/vprunet/src/PNM/camtrap_23/data
8 user accounts
authentification: BasicAuth
Dash is running on http://0.0.0.0:8050/

 * Serving Flask app 'camtrap'
 * Debug mode: on

```

Comme on n'a pas encore traité les médias avec megadetector, il faut décocher la case de filtrage megadetector. On peut parcourir les médias et créer des observations.

```
 /home/vprunet/src/microsoft/MDv5/venv/bin/python /home/vprunet/src/microsoft/MDv5/src/foo.py -p test -r /home/vprunet/camtrap/test
```

-r ne sert à rien ici

```
/home/vprunet/src/microsoft/MDv5/venv/bin/python /home/vprunet/src/microsoft/MDv5/src/bar.py -p test -r /home/vprunet/camtrap/test
```

L'appli enregistre les observations avec un id de projet erroné.
