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
