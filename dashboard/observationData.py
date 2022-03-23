from pathlib import Path
import json
from config import data_root
from dataFinder import *
import time


def summary(visit, site_id):
    path = data_root/'observations'/str(site_id)/visit
    if not path.exists():
        return []
    return [obs.stem for obs in path.iterdir()]


def details(visit, site_id):
    def getObsAux(path):
        try:
            with path.open('r') as f:
                return json.load(f)
        except:
            print('Error: observationData.details: cannot decode observation', path)
            return None
    path = data_root/'observations'/str(site_id)/visit
    if not path.exists():
        return []
    return [(p.stem, getObsAux(p)) for p in path.iterdir()]


def getObservation(media, visit, site_id):
    # TODO add timestamp to observation filename
    path = data_root/'observations'/str(site_id)/visit
    path.mkdir(parents=True, exist_ok=True)
    try:
        with (path/(media + '.json')).open('r') as f:
            obs = json.load(f)
            return obs
    except:
        return {'attributes': {}}


def putObservation(obs, media, visit, site_id):
    path = data_root/'observations'/str(site_id)/visit
    path.mkdir(parents=True, exist_ok=True)
    try:
        with (path/(media + '.json')).open('w') as f:
            json.dump(obs, f)
    except:
        print('Error:writeObservation', path, media, obs)


def loadClassifier(site_id, visit, media):
    "loads media classification from file. Creates file if needed"
    path = data_root/'classification'/'media' / \
        str(site_id)/visit/(media + '.json')
    try:
        with path.open('r') as f:
            classifier = json.load(f)
    except:
        classifier = dict(version=1, serial=0)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w') as f:
            json.dump(classifier, f)
    return classifier


def dumpClassifier(classifier, site_id, visit, media):
    "Assumes that classifier has been loaded before, no check on version here"
    path = data_root/'classification'/'media' / \
        str(site_id)/visit/(media + '.json')
    old_classifier = loadClassifier(site_id, visit, media)
    if classifier['serial'] < old_classifier['serial']:
        print(f'dumpClassifier: abort : {path}')
        print(f'    old (retained) <<< {old_classifier}')
        print(f'    new (discarded) <<< {classifier}')
        return False
    classifier['serial'] += 1
    classifier['version'] = 1
    with path.open('w') as f:
        json.dump(classifier, f)
    return True


def filter(metadata, parameters, visit, site_id):
    p = parameters['subparameters']

    def filter_obs(obs):
        a = obs['attributes']
        if p['valid'] and not a.get('valid'):
            return False
        if p['not_valid'] and a.get('valid'):
            return False
        if p['notify'] and not a.get('notify'):
            return False
        if p['not_notify'] and a.get('notify'):
            return False
        if p['empty'] and not a.get('empty'):
            return False
        if p['not_empty'] and a.get('empty'):
            return False
        if p['species'] and a.get('species') not in p['species']:
            return False
        return True

    if parameters['processed']:
        observations = details(visit, site_id)
        filtered = [md for md in metadata for (
            filename, obs) in observations if (md['fileName'] == filename and filter_obs(obs))]
    else:
        excluded_media = summary(visit, site_id)
        filtered = [md for md in metadata if md['fileName']
                    not in excluded_media]
    return filtered


if __name__ == '__main__':
    s = summary('2020-08-30', 101)
    print(s)
