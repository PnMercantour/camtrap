Essai de fonctionnement avec un client distant.

Configuration LAN et VPN
L'application est réactive dans les deux cas.
En mode LAN, les vidéos se chargent instantanément.
En mode VPN, le chargement des vidéos est très lent.

Architecture mise en place:
charger la vidéo depuis un autre serveur (typiquement un serveur http adhoc sur ou à proximité de la machine cliente). Ca marche.

sur windows,  installer python3
cd dans le répertoire racine des vidéos.
python3 -m http.server

paramétrer l'url des médias dans les préférences de l'application, par défaut http://localhost:8000