from pathlib import Path
import json
import argparse
from config import data_root
from metadata import listSites, listVisits


def getVisitData(visit, site_id):
    path = (data_root / 'detection' / 'megadetector' /
            str(site_id) / visit).with_suffix('.json')
    if (not path.exists()):
        return buildData(visit, site_id)
    with path.open('r') as f:
        md = json.load(f)
        return md


def buildData(visit, site_id):
    source = data_root / 'detection' / 'frames' / \
        ('Maille ' + str(site_id)) / visit
    if not source.exists():
        print(f'megadetectorData.buildData: {source} does not exist')
        return
    l = []
    d = {}
    for p in source.iterdir():
        if p.suffix != '.json':
            continue
        try:
            [video, frame] = p.stem.split('-')
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
    dest_dir = data_root / 'detection' / 'megadetector' / str(site_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with (dest_dir / visit).with_suffix('.json').open('w') as f:
        json.dump(d, f)
    return d


if __name__ == '__main__':
    print('Rebuilding megadetector data')
    for site_id in listSites():
        for visit in listVisits(site_id):
            buildData(visit, site_id)
    print('Done!')
