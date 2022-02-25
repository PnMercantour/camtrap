classifier

statut de l'observation

- validée
- signalée (manque un taxon, autre problème)
- media à supprimer

Info Site (mettre le nom du site dans le label)

# Filtre
ajouter un switch: inclure les déclenchements intempestifs

ajouter un filtre date

ajouter un filtre observation
- média non annoté
- espèce
- statut de l'obs (validée, non validée)
- observation signalée


Seuil de détection : essayer input,

Media : slider pour voir la position du media dans la visite (1 à nbre de medias, valeur courante) encadré par boutons previous /next
slider pour voir la position du media dans le groupe (1 à nbre de medias). encadré par boutons first/last
Groupe : slider pour voir la position du groupe dans la visite (1 à nbre de groupes) encadré par boutons groupe précédent, groupe suivant

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
- les callback dash sont optimisées pour limiter le volume  de données dans le sens client -> serveur. En conséquence, le résultat des requêtes est caché sur le serveur, et le client ne transmet que les informations nécessaires pour faire la requête (et profiter du cache de mémoïsation).
