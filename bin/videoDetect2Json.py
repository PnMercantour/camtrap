"""
Batch processor for video files.
Runs megadetector on each file then stores results into json files
"""
import cv2
from PIL import Image
from os import getenv
import time
import json
from pathlib import Path
import humanfriendly
import argparse
from detection.run_tf_detector import TFDetector


def processVideo(path, json_dir, tf_detector, first_frame=0, last_frame=None, pick=1, overwrite=False):
    if not path.is_file():
        print(path, 'not a file')
        return
    print(f'Processing video {path}')
    if path.suffix != '.MP4':
        print(path, 'unknown suffix')
        return
    cap = cv2.VideoCapture(str(path))
    num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    first_frame = max(0, min(first_frame, num_frames - 1))
    last_frame = min(
        num_frames - 1, last_frame) if last_frame else num_frames - 1
    pick = max(pick, 1)

    frame = first_frame
    while frame <= last_frame:
        print(f'Processing image {path}:{frame}')
        json_file = json_dir / (path.name + '-'+str(frame) + '.json')
        if overwrite or not json_file.exists():
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
            success, image = cap.read()
            if success:
                pil_image = Image.fromarray(
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                # pil_image.show()
                result = tf_detector.generate_detections_one_image(
                    pil_image, frame)
                with open(json_dir / (path.name + '-'+str(frame) + '.json'), 'w') as f:
                    json.dump(result, f, indent=1)
        frame = frame + pick
    cap.release()


def processPath(path, root, output, tf_detector, first_frame, last_frame, pick, overwrite):
    if not path.exists():
        print(f'{path} does not exist')
        return
    if path.is_file():
        relative = path.parent.relative_to(root)
    else:
        relative = path.relative_to(root)
    json_dir = output / relative
    print(f'Output to {json_dir}')
    json_dir.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        processVideo(path, json_dir, tf_detector,
                     first_frame, last_frame, pick, overwrite)
    else:
        for p in path.iterdir():
            if p.is_file():
                processVideo(p, json_dir,  tf_detector,
                             first_frame, last_frame, pick, overwrite)
            if p.is_dir():
                processPath(p, root, output, tf_detector,
                            first_frame, last_frame, pick, overwrite)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""
Batch processor for video files.
Runs megadetector on each file then stores results into json files""")
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth frame', type=int, default=6)
    parser.add_argument(
        '--overwrite', help='overwrite existing results', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--detector_file', default=getenv('MEGADETECTOR'))
    parser.add_argument(
        '-r', '--root', help='base directory for source files', type=Path, default='')
    parser.add_argument(
        '-o', '--output', help='base directory for output files', type=Path, default='output')
    parser.add_argument('video', nargs='+',
                        help='source video folder or file', type=Path)

    args = parser.parse_args()
    print(args)
    start_time = time.time()
    print('Loading model:', args.detector_file)
    tf_detector = TFDetector(args.detector_file)
    elapsed = time.time() - start_time
    print('Loaded model (batch level) in {}'.format(
        humanfriendly.format_timespan(elapsed)))

    for path in args.video:
        processPath(path, args.root, args.output,  tf_detector, args.first_frame,
                    args.last_frame, args.pick, args.overwrite)
