"""Utility functions to access raw and processed data files.
Hierarchical data storage:
root: root path of the repository,
id: #id of a Maille, relative path name from root is 'Maille <id>'
date: date of a visit, relative path name from Maille is an ISO formatted date string 'YYYY-mm-DD'
asset: filename of a photo/video/audio/json file
"""

from pathlib import Path
from datetime import date


def df_ids(root):
    "Sorted maille ids under root"
    l = []
    for element in root.iterdir():
        split = element.name.split(' ')
        if split[0] == 'Maille':
            l.append(int(split[1]))
    l.sort()
    return l


def df_id_path(id, root=Path('.')):
    "Maille path from maille id"
    return root / f'Maille {id}'


def df_dates(id_path):
    " Sorted list of visit dates for given Maille id path, most recent first"
    l = []
    for visit in id_path.iterdir():
        try:
            date.fromisoformat(visit.name)
            l.append(visit.name)
        except:
            print(f'warning:df-dates:invalid repository: {visit}: ignored')
    l.sort(reverse=True)
    return l


def df_date_path(date, id_path):
    "visit path from visit date and Maille path"
    return id_path / date


def df_assets(date_path):
    "Sorted list of assets attached to a given date path"
    l = []
    for file in date_path.iterdir():
        l.append(file.name)
    l.sort()
    return l


def df_asset_path(name, date_path):
    "Asset path from asset name and date path"
    return date_path / name


if __name__ == '__main__':
    root = Path('data/video')
    ids = df_ids(root)
    print(ids)
    id = ids[0]
    id_path = df_id_path(id, root)
    dates = df_dates(id_path)
    print(dates)
    date = dates[0]
    date_path = df_date_path(date, id_path)
    assets = df_assets(date_path)
    for asset in assets:
        print(df_asset_path(asset, date_path))
