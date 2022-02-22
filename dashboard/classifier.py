from pathlib import Path
import json
from config import data_root
from dataFinder import *
import time


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


if __name__ == '__main__':
    data_root = Path('data/test')
    c = loadClassifier(6, '2020-03-11', 'IMG_0002.MP4')  # version 0
    d = loadClassifier(6, '2020-03-11', 'IMG_0002.MP4')  # version 0
    print(c)
    c['foo'] = 'bar'
    dumpClassifier(c, 6, '2020-03-11', 'IMG_0002.MP4'
                   )  # bump to version 1
    e = loadClassifier(6, '2020-03-11', 'IMG_0002.MP4')
    print(e)
    dumpClassifier(d, 6, '2020-03-11', 'IMG_0002.MP4')  # rejected
