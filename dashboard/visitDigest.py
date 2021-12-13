from pathlib import Path
import json
import argparse
from dataFinder import *


def visitDigest(path, first_frame=0, last_frame=None):
    """Aggregate JSON image reports from a given location/collection date"""
    if not path.exists():
        print(f'{path} does not exist')
        return
    d = {}
    for p in path.iterdir():
        if p.suffix != '.json':
            continue
        try:
            [video, frame] = p.stem.split('-')
            if int(frame) < first_frame:
                continue
            if last_frame is not None and int(frame) > last_frame:
                continue
            report = d.setdefault(video, dict(
                max_detection_conf=0, frames=[], empty_frames=[]))
            with open(p, 'r') as f:
                frame_report = json.load(f)
                report['frames'].append(frame)
                if frame_report['max_detection_conf'] == 0:
                    report['empty_frames'].append(frame)
                else:
                    report['max_detection_conf'] = max(
                        report['max_detection_conf'], frame_report['max_detection_conf'])
                    for detection in frame_report["detections"]:
                        category = detection["category"]
                        report[category] = max(
                            report.get(category, 0), detection['conf'])
        except:
            print('cannot decode file name or payload', p)
    return d


def processMaille(id, from_path, to_path):
    id_path = df_id_path(id, from_path)
    id_to_path = df_id_path(id, to_path)
    id_to_path.mkdir(parents=True, exist_ok=True)
    dates = df_dates(id_path)
    for d in dates:
        digest = visitDigest(df_date_path(d, id_path))
        with (id_to_path / (d + '.json')).open('w') as f:
            json.dump(digest, f)


def processData(from_path, to_path):
    to_path.mkdir(parents=True, exist_ok=True)
    for id in df_ids(from_path):
        processMaille(id, from_path, to_path)


def readFromCache(path, id, date):
    with (df_id_path(id, path) / (date + '.json')).open() as f:
        digest = json.load(f)
    return digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Build visit JSON digest reports.")
    parser.add_argument(
        '-j', '--json', help='output as JSON', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        '-d', '--data', help='source folder for JSON reports', type=Path, default=Path('data/detection/frames'))
    parser.add_argument(
        '-o', '--output', help='destination folder for JSON reports', type=Path, default=Path('data/detection/visits'))
    parser.add_argument('-f', '--first_frame',
                        help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    args = parser.parse_args()

    processData(args.data, args.output)
