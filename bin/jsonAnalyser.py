from pathlib import Path
import json
import argparse


def aggregateImageReports(path, first_frame=0, last_frame=None):
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
                max_detection_conf=0, num_frames=0, empty_frames=0))
            with open(p, 'r') as f:
                frame_report = json.load(f)
                report['num_frames'] = report['num_frames'] + 1
                if frame_report['max_detection_conf'] == 0:
                    report['empty_frames'] = report['empty_frames'] + 1
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


def detailedVideoReport(path, selected_video, first_frame=0, last_frame=None):
    """Detailed report for a given video file"""
    if not path.exists():
        print(f'{path} does not exist')
        return
    report = dict(
        max_detection_conf=0, num_frames=0, empty_frames=0, frames=[])
    for p in path.iterdir():
        if p.suffix != '.json':
            continue
        try:
            [video, frame] = p.stem.split('-')
            if video != selected_video:
                continue
            if int(frame) < first_frame:
                continue
            if last_frame is not None and int(frame) > last_frame:
                continue
            with open(p, 'r') as f:
                frame_report = json.load(f)
                report["frames"].append(frame_report)
                report['num_frames'] = report['num_frames'] + 1
                if frame_report['max_detection_conf'] == 0:
                    report['empty_frames'] = report['empty_frames'] + 1
                else:
                    report['max_detection_conf'] = max(
                        report['max_detection_conf'], frame_report['max_detection_conf'])
                    for detection in frame_report["detections"]:
                        category = detection["category"]
                        report[category] = max(
                            report.get(category, 0), detection['conf'])
        except:
            print('cannot decode file name or payload', p)
    return report


def analyzeAggregatedReport(d):
    video_count = 0
    empty_video = 0
    no_animal = 0
    not_main_subject = 0
    under_threshold = 0
    human_in_video = 0
    detected_animal = 0
    selected_video = []
    for (video, report) in d.items():
        video_count += 1
        if report['empty_frames'] == report['num_frames']:
            empty_video += 1
        elif report.get('1', 0) == 0:
            no_animal += 1
        elif report['1'] < report['max_detection_conf']:
            not_main_subject += 1
        elif report['1'] < 0.5:
            under_threshold += 1
        elif report.get('2', 0) > 0.5:
            human_in_video += 1
        else:
            detected_animal += 1
            selected_video.append(video)
    return(dict(video_count=video_count, empty_video=empty_video, no_animal=no_animal, not_main_subject=not_main_subject, under_threshold=under_threshold, human_in_video=human_in_video, detected_animal=detected_animal))


# data_dir = Path('output/Maille 6/2020-08-27')

# summary = aggregateImageReports(data_dir)
# detail = detailedVideoReport(data_dir, 'IMG_0584.MP4')
# print(f'max detection confidence: {detail["max_detection_conf"]}')
# for frame in detail["frames"]:
#     print(frame)
# print(json.dumps(detail, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Analyse JSON reports.")
    parser.add_argument(
        '-j', '--json', help='output as JSON', action=argparse.BooleanOptionalAction, default=True)

    parser.add_argument(
        '-v', '--video', help='detailed video report')
    parser.add_argument(
        'dir', help='source folder for JSON reports', type=Path)
    parser.add_argument('-f', '--first_frame',
                        help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    args = parser.parse_args()
    if args.video is not None:
        print(json.dumps(detailedVideoReport(args.dir, args.video,
              args.first_frame, args.last_frame), indent=2))
    else:
        print(json.dumps(analyzeAggregatedReport(
            aggregateImageReports(args.dir, args.first_frame, args.last_frame)), indent=2))
