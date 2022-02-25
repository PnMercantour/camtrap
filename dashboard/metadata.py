from pathlib import Path
import json
from config import data_root
from dataFinder import *
from datetime import datetime, timedelta
from functools import lru_cache

exiftoolDateFormat = '%Y:%m:%d %H:%M:%S'


def listSites():
    l = []
    for site in (data_root / 'metadata' / 'sites').iterdir():
        try:
            l.append(int(site.name))
        except:
            print(f'waning:listSites:invalid site id: {site}: ignored')
    l.sort()
    return l


def listVisits(site_id):
    " Sorted list of visit dates for given site id, most recent first"
    l = []
    for visit in (data_root/'metadata'/'sites'/str(site_id)).iterdir():
        try:
            date.fromisoformat(visit.stem)
            l.append(visit.stem)
        except:
            print(f'warning:listVisits:invalid visit header: {visit}: ignored')
    l.sort(reverse=True)
    return l


def getVisitMetadata(visit, site_id):
    path = (data_root / 'metadata' / 'sites' /
            str(site_id) / visit).with_suffix('.json')
    if (not path.exists()):
        return buildMetadata(visit, site_id)
    with path.open('r') as f:
        md = json.load(f)
        return md


@lru_cache  # for improved memory usage (not for performance)
def getVisitMetadataFromCache(visit, site_id):
    return getVisitMetadata(visit, site_id)


def buildMetadata(visit, site_id):
    exif_path = data_root / 'exif' / ('Maille ' + str(site_id)) / visit
    if not exif_path.exists():
        print(f'buildMetadata: {exif_path} does not exist')
        return
    l = []
    for p in exif_path.iterdir():
        if p.suffix != '.json':
            continue
        with p.open('r') as f:
            md = json.load(f)[0]
            l.append(dict(
                fileName=md['File:FileName'],
                path=md["SourceFile"],
                startTime=(datetime.strptime(
                    md["QuickTime:MediaCreateDate"], exiftoolDateFormat)).isoformat(),
                duration=md["QuickTime:TrackDuration"]
            ))
    l.sort(key=lambda media: media['startTime'])
    dest_dir = data_root / 'metadata' / 'sites' / str(site_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with (dest_dir / visit).with_suffix('.json').open('w') as f:
        json.dump(l, f)
    return l


def groupMedia(metadata, interval):
    """  Group media when end time /start time difference is smaller than interval (a number of seconds). metadata MUST be sorted"""
    delta = timedelta(seconds=interval)
    g = None
    groups = []
    end_time = None
    for media in metadata:
        start_time = datetime.fromisoformat(media['startTime'])
        if end_time is None or end_time + delta < start_time:
            g = dict(metadata=[media], startTime=media['startTime'])
            groups.append(g)
        else:
            g['metadata'].append(media)
        end_time = start_time + timedelta(seconds=media['duration'])
        g['endTime'] = end_time.isoformat()
    return groups


if __name__ == '__main__':
    root = Path('data')
    for site in (root / 'exif').iterdir():
        split = site.name.split(' ')
        if split[0] == 'Maille':
            site_id = split[1]
            for visit in site.iterdir():
                try:
                    date.fromisoformat(visit.name)
                    buildMetadata(visit.name, site_id, root)
                except:
                    print(f'warning:invalid repository: {visit}: ignored')
