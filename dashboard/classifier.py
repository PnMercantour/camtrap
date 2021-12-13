from pathlib import Path
import json
from dataFinder import *
import time


def loadClassifier(path, id, date, name):
    "read classifier from file."
    try:
        with df_asset_path(f'{name}_classif.json', df_date_path(date, df_id_path(id, path))).open() as f:
            classifier = json.load(f)
    except:
        classifier = dict(protocol=1, version=0)
    return classifier


def storeClassifier(classifier, path, id, date, name):
    date_path = df_date_path(date, df_id_path(id, path))
    date_path.mkdir(parents=True, exist_ok=True)
    file_path = df_asset_path(f'{name}_classif.json', date_path)
    if file_path.exists():
        with file_path.open() as f:
            old_classifier = json.load(f)
        if classifier['version'] < old_classifier['version']:
            print(f'storeClassifier: abort update: {file_path}, {classifier}')
            return
    classifier['version'] += 1
    with file_path.open('w') as f:
        json.dump(classifier, f)


if __name__ == '__main__':
    p = Path('data/classification/video')
    c = loadClassifier(p, 6, '2020-03-11', 'IMG_0002.MP4')  # version 0
    d = loadClassifier(p, 6, '2020-03-11', 'IMG_0002.MP4')  # version 0
    print(c)
    c['foo'] = 'bar'
    storeClassifier(c, p, 6, '2020-03-11', 'IMG_0002.MP4')  # bump to version 1
    e = loadClassifier(p, 6, '2020-03-11', 'IMG_0002.MP4')
    print(e)
    storeClassifier(d, p, 6, '2020-03-11', 'IMG_0002.MP4')  # rejected
