from pathlib import Path
from datetime import date
import json

from config import data_root
import metadata


def stats(user=None, species=None, site=None, from_date=None, to_date=None):
    obs_list = []
    obs_root_path = data_root / 'observations'
    for site_dir in obs_root_path.iterdir():
        for visit_dir in site_dir.iterdir():
            md = metadata.getVisitMetadata(visit_dir.name, site_dir.name)
            index = {}
            for item in md:
                index[item['fileName']] = item
            for observation_file in visit_dir.iterdir():
                timestamp = observation_file.stat().st_mtime
                with observation_file.open('r') as f:
                    obs = json.load(f)
                obs['timestamp'] = timestamp
                obs['media'] = observation_file.relative_to(
                    obs_root_path).with_suffix('')
                obs['date'] = index[obs['media'].name]['startTime']
                obs_list.append(obs)
    return obs_list


obs_list = stats()

species = {}
domestic = {}
user = {}
register = {}
for obs in obs_list:
    observed = obs['attributes']['species']
    if observed:
        species[observed] = species.get(observed, 0) + 1
    observed = obs['attributes']['domestic']
    if observed:
        domestic[observed] = domestic.get(observed, 0) + 1
    user[obs['user']] = user.get(obs['user'], 0) + 1
    registration = date.isoformat(date.fromtimestamp(obs['timestamp']))
    register[registration] = register.get(registration, 0) + 1

print(len(obs_list), "fiches d'observation")
print("Observations d'espèces sauvages")
for e, n in species.items():
    print('\t', n, '\t', e)
print()
print("Observations d'espèces domestiques")
for d, n in domestic.items():
    print('\t', n, '\t', d)
print()
print('Observateurs')
for name, n in user.items():
    print('\t', n, '\t', name)
print()
print("Saisies d'observations par date")
for d in sorted(list(register)):
    print('\t', register[d], '\t', d)
