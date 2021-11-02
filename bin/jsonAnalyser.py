from pathlib import Path
import json

data_dir = Path('/Users/vincent/Downloads/camtrap/2020-04-22')

d = {}
for path in data_dir.iterdir():
    if path.suffix != '.json':
        continue
    try:
        [video, frame] = path.stem.split('-')
        report = d.setdefault(video, dict(
            max_detection_conf=0, num_frames=0, empty_frames=0))
        with open(path, 'r') as f:
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
        print('cannot decode file name or payload', path)
video_count = 0
empty_video = 0
no_animal = 0
not_main_subject = 0
unlikely = 0
human_in_video = 0
detected_animal = 0
for (video, report) in d.items():
    video_count += 1
    if report['empty_frames'] == report['num_frames']:
        empty_video += 1
    elif report.get('1', 0) == 0:
        no_animal += 1
    elif report['1'] < report['max_detection_conf']:
        not_main_subject += 1
    elif report['1'] < 0.5:
        unlikely += 1
    elif report.get('2', 0) > 0.5:
        human_in_video += 1
    else:
        detected_animal += 1
        print(video, report)

print('video count', video_count)
print('empty video', empty_video)
print('No animal in video', no_animal)
print('not most likely', not_main_subject)
print('unlikely', unlikely)
print('human in video', human_in_video)
print('detected animal', detected_animal, detected_animal/video_count)
