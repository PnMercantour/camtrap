from pathlib import Path
import json
import argparse
from dataFinder import *
from datetime import datetime, timedelta

exiftoolDateFormat = '%Y:%m:%d %H:%M:%S'


def metadata(path):
    """Load and sort media metadata, path is a visit metadata folder"""
    if not path.exists():
        print(f'{path} does not exist')
        return
    l = []
    for p in path.iterdir():
        if p.suffix != '.json':
            continue
        with open(p, 'r') as f:
            md = json.load(f)[0]
            l.append(dict(mdFile=p, fileName=md['File:FileName'], path=md["SourceFile"], startTime=datetime.strptime(
                md["QuickTime:MediaCreateDate"], exiftoolDateFormat), duration=timedelta(seconds=md["QuickTime:TrackDuration"])))
    l.sort(key=lambda media: media['startTime'])
    return l


def groupMedia(metadata, interval):
    """  Group media when end time /start time difference is smaller than interval (a number of seconds). metadata MUST be sorted"""
    delta = timedelta(seconds=interval)
    g = None
    groups = []
    for media in metadata:
        if g is not None and g['endTime'] + delta > media['startTime']:
            g['metadata'].append(media)
        else:
            g = dict(metadata=[media], startTime=media['startTime'])
            groups.append(g)
        g['endTime'] = media['startTime'] + media['duration']
    return groups


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Build visit JSON digest reports.")
    parser.add_argument('-d', '--delta', type=int, default=60)
    parser.add_argument(
        'exifFolder', help='source folder for exif JSON reports', type=Path)
    args = parser.parse_args()

    groups = groupMedia(metadata(args.exifFolder), args.delta)
    for group in groups:
        print(group)
    print('number of groups =', len(groups))
