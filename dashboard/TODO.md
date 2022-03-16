classifier

statut de l'observation

- validée
- signalée (manque un taxon, autre problème)
- media à supprimer

# metadata

Supprimer le module obsolète dataFinder

# data

Enrichir config/megadetector.json (seuils, ...)

# Sélection

Info Site (mettre le nom du site dans le label)
ajouter le nombre de médias dans la sélection (avant filtrage)

Si les perf le permettent, déplacer le sélecteur visite du côté média
Intérêt : le filtrage serait appliqué à toutes les visites du site.

# Filtre

ajouter un filtre date

ajouter un filtre observation

- média non annoté
- espèce
- statut de l'obs (validée, non validée)
- observation signalée
  Filtre : obs validées, obs signalées, les obs de x... défaut : mes obs.

## megadetector

ajouter un switch: déclenchements intempestifs (lorsque rien n' été détecté)
Seuil de détection : essayer input, étendre la précision

# Media

slider pour voir la position du media dans la visite (1 à nbre de medias, valeur courante) encadré par boutons previous /next

slider pour voir la position du media dans le groupe (1 à nbre de medias). encadré par boutons first/last

Groupe : slider pour voir la position du groupe dans la visite (1 à nbre de groupes) encadré par boutons groupe précédent, groupe suivant

TODO ajouter intervalle 1 jour, 1 mois, pour permettre des saisies en bloc (media vides, etc ...)

Recalage sur la vidéo la plus proche :

- si humain sur dernière vidéo sans filtre, l'introduction du filtre recale sur la première vidéo car il n'y a pas de vidéo suivante. Corriger et caler sur la vidéo précédente.

# Observation

La carte observation contient les données d'observation saisies par un agent.
A la lecture, l'observation la plus récente est chargée en mémoire.

A terme : voir l'historique des observations.

Statut: validé ou pas.
Statut: signaler une obs.

## Initialisation de la fiche

lire la valeur définie dans les préférences de appliquer au groupe
si elle vaut False, lire la fiche la plus récente du média
sinon lire la fiche les plus récente de chacun des médias du groupe. Si des valeurs diffèrent ou sont absentes dans les autres fiches du groupe, forcer appliquer au groupe à False.

### Valeurs en sortie

    Enregistrer : inactif
    annuler: inactif
    cookie initial_state: copie de la fiche (y compris booléen appliquer au groupe)
    attributs : attributs du média courant

## Modification d'un attribut (ou de plusieurs attributs, possible si copy/paste) :

comparaison avec initial_state (la valeur de appliquer au groupe n'est prise en compte dans la comparaison que si elle vaut False dans l'état initial)

    Enregistrer devient actif si initial_state et état courant diffèrent, sinon inactif
    annuler est actif si initial_state et état courant diffèrent, sinon inactif

## Enregistrer

Enregistre la fiche ou le groupe de fiches et bascule dans l'état initial (relecture de la ou des fiches, etc...)

L'identifiant de l'utilisateur courant est enregistré.
Tous les attributs qui ont une valeur non nulle sont enregistrés.

L'observation est identifiée par le média et le timestamp (on ne considère pas le cas fort improbable et sans conséquence dans lequel deux enregistrements seraient réalisés exactement au même moment).

Pour mémoire, les observations précédentes sont conservées sur le backend, pour pouvoir reconstituer l'historique (évolutions futures) et éventuellement restaurer à la main les données écrasées par erreur.

## Annuler

Réinitialise la fiche.

## Copier

Copie les attributs de la fiche courante (y compris) dans le cookie copy/paste

## Coller

Colle dans la fiche courante le contenu du cookie copy/paste. Le cookie copy/paste n'est ps modifié.

## Modification dans l'écran Préférences

Ne rien faire (la valeur de la préférence `appliquer au groupe` n'est pas prise en compte pour l'édition en cours).

## détail de la fiche

Plusieurs espèces (bouton)
confirmation/infirmation megadetector
video à supprimer
présentation hiérarchique des espèces
mâle/femelle
espèces domestiques
uuid

# Video

positionner la vidéo aux instants clé et/ou concaténer les vidéos d'un même groupe.

https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/currentTime

https://wicg.github.io/controls-list/html-output/multipage/embedded-content.html#attr-media-controlslist

Conservation des vidéos vides :
intérêt historique (végétation, manteau neigeux, ...)
Voir avec Jérome.

# Activer https sur le serveur origin

Camtrap permet de lire les médias depuis une autre source que l'origine (http(s)://camtrap.mercantour-parcnational.fr), dès lors qu'un serveur http de médias est configuré sur la machine cliente (localhost) ou sur un serveur local (sur le lan). Cette fonctionnalité de camtrap est essentielle, en effet:

- le serveur applicatif est hébergé dans le cloud, et n'a pas la capacité de stocker et de servir plusieurs To de données vidéo. L'utilisation de serveurs spécialisés n'est pas une option viable à l'heure actuelle pour des raisons de coût et de difficulté à pousser les médias dans le cloud (voir le point suivant)
- les clients de l'application disposent d'une bande passante limitée (type adsl) en lecture (download) et plus encore en écriture (upload), le chargement d'une vidéo de 30s (90Mo) serait rédhibitoire pour l'interactivité et la rapidité de traitement. Pousser les médias dans le cloud (voir point précédent) est inenvisageable.

Le bon fonctionnement de cette option de camtrap
On ne peut activer https sur le serveur origine que si on sait comment autoriser le chargement des vidéos depuis un site non https (localhost ou un serveur sur le lan) ou qu'on active également https pour le serveur lan.

## mixed content

Lorsque le site principal est https et que le serveur de médias est http, on parle de mixed content.

https://w3c.github.io/webappsec-mixed-content/
https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content

https://support.mozilla.org/en-US/kb/mixed-content-blocking-firefox

## https sur le lan

On peut activer https sur un serveur lan, sous réserve que l'on configure correctement le navigateur qui va l'interroger.

https://www.techrepublic.com/article/how-to-add-a-trusted-certificate-authority-certificate-to-chrome-and-firefox/

accéder aux vidéos sur un serveur local.

Le serveur doit respecter les nouvelles spécifications du CORS ou le navigateur doit être paramétré pour ignorer ces spécifications.

chrome://flags/#block-insecure-private-network-requests

https://stackoverflow.com/questions/66534759/chrome-cors-error-on-request-to-localhost-dev-server-from-remote-site

https://developer.chrome.com/blog/private-network-access-update/

https://developer.chrome.com/blog/private-network-access-preflight/

https://mozilla.github.io/standards-positions/#cors-and-rfc1918
https://gist.github.com/acdha/925e9ffc3d74ad59c3ea

https://developer.mozilla.org/fr/docs/Web/HTTP/Methods/OPTIONS

Firefox linux

décodage logiciel
https://askubuntu.com/questions/1274143/firefox-not-playing-videos-on-ubuntu-20-04-4-lts

Installer une lib pour décoder les media mp4

```
sudo apt install ffmpeg
``̀̀̀

Le décodage matériel des vidéos nécessite une configuration supplémentaire:
https://discourse.ubuntu.com/t/enabling-accelerated-video-decoding-in-firefox-on-ubuntu-21-04/22081


Architecture

Sélection : gestion des paramètres site (site_id: number) et visite (visit: ISO date string).
Les visites sont ordonnées de la plus récente à la plus ancienne.

Filtrage (détection) : paramètres du filtre appliqué aux metadonnées de la visite. On peut filtrer sur les résultats du megadetector, les observations, ...

Media : liste filtrée des medias , media sélectionné, boutons pour l'exploration des medias (premier (du groupe), dernier (du groupe), précédent, suivant)
premier média et dernier média du groupe sont inactifs lorsque la position est atteinte.
précédent (suivant) est inactif lorsque le premier (dernier) média est déjà sélectionné.

Groupe : Regroupement des media selon un intervalle paramétrable. Boutons groupe précédent/suivant qui positionnent le media sur le premier média du groupe sélectionné.
Boutons inactifs lorsque la limite est atteinte.

Performances
Optimisé pour fonctionner avec une connexion internet peu performante (du type ADSL).

- les media peuvent être accédés localement sur le site client plutôt que téléchargés depuis un serveur distant.
- les callback dash sont optimisées pour limiter le volume de données dans le sens client -> serveur. En conséquence, le résultat des requêtes est caché sur le serveur, et le client ne transmet que les informations nécessaires pour faire la requête (et profiter du cache de mémoïsation).
```

Application cliente

camtrap est une application web, qui peut être utilisée depuis un navigateur web. Cette architecture garantit:

- que tous les utilisateurs utilisent la même version de l'application
- que les données sont gérées de façon centralisée et que la base de données est protégée contre les accès directs depuis un client
- que les utilisateurs sont authentifiés et autorisés à accéder à l'application.

de façon optionnelle, une extension peut être installée sur ou à proximité de l'ordinateur client pour fournir un accès rapide aux médias.

L'extension propose les fonctionnalités suivantes:

- serveur de médias
- serveur d'images extraites d'un média
- check media (compare la liste des médias sur le serveur local à la base de données centrale). Check media peut être utilisé pour filtrer l'affichage des données disponibles sur le serveur courant.
- mise à jour des données médias (effacement de médias sans intérêt, redimensionnement)
