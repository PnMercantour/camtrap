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
        suffixes = p.suffixes
        if len(suffixes) < 2 or suffixes[-1] != '.json':
            print('megadetectorData', p, 'ignored')
            continue
        try:
            # decode videoNN.MP4-FF.json filenames where FF is a frame number
            [media_type, frame_str] = suffixes[-2].split('-')
            frame = int(frame_str)
        except:
            # decode photoNN.JPG.json filenames
            media_type = suffixes[-2]
            frame = None
        try:
            if media_type in ['.MP4']:
                video = p.stem.split('-')[0]
                report = d.setdefault(video, dict(
                    media_type=media_type, max_detection_conf=0, frames=[], empty_frames=[]))
                with p.open('r') as f:
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
            elif media_type in ['.JPG']:
                photo = p.stem
                with p.open('r') as f:
                    photo_report = json.load(f)
                    report = dict(
                        media_type=media_type, max_detection_conf=photo_report['max_detection_conf'])
                    for detection in photo_report['detections']:
                        category = detection["category"]
                        report[category] = max(
                            report.get(category, 0), detection['conf'])
                    d[photo] = report
            else:
                print('megadetectorData:', p, 'unhandled media type')
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
