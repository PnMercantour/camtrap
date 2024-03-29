"""
Batch processing of media files with megadetector.
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


def processMedia(path, relative, json_dir, image_dir, tf_detector, first_frame=0, last_frame=None, pick=None, custom=None, overwrite=False, dump=False):
    if not path.is_file():
        print(path, 'not a file')
        return
    print(f'Processing media {path}')
    if path.suffix in ['.jpg', '.JPG']:
        json_file = json_dir / f'{path.name}.json'
        if overwrite or not json_file.exists():
            try:
                pil_image = Image.open(path)
                result = tf_detector.generate_detections_one_image(
                    pil_image, str(relative / path.name))
                with open(json_file, 'w') as f:
                    json.dump(result, f)
            except:
                print('Error:processMedia: invalid image file', path)
        return
    if path.suffix not in ['.MP4', '.mp4']:
        print(path, 'unhandled media format')
        return
    if custom and not overwrite and not dump:
        # optimization: avoid loading media if all custom frames have been processed in a previous run
        # warning: last frame and pick are not checked
        if all([(json_dir / f'{path.name}-{frame}.json').exists() for frame in custom]):
            # print(path)
            return
    cap = cv2.VideoCapture(str(path))
    num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if custom:
        for frame in custom:
            image_file = f'{path.name}-{frame}.jpg'
            relative_image_path = relative / image_file
            print(f'Processing image {relative_image_path}')
            json_file = json_dir / f'{path.name}-{frame}.json'
            if overwrite or not json_file.exists() or dump:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                success, image = cap.read()
                if success:
                    pil_image = Image.fromarray(
                        cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    # pil_image.show()
                    if overwrite or not json_file.exists():
                        result = tf_detector.generate_detections_one_image(
                            pil_image, str(relative_image_path))
                        with open(json_file, 'w') as f:
                            json.dump(result, f)
                    if dump:
                        pil_image.save(image_dir/image_file)
    first_frame = max(0, min(first_frame, num_frames - 1)
                      )if first_frame is not None else 0
    last_frame = min(
        num_frames - 1, last_frame) if last_frame else num_frames - 1
    pick = max(pick, 1)if pick else int(num_frames / 2)

    frame = first_frame
    while frame <= last_frame:
        image_file = f'{path.name}-{frame}.jpg'
        relative_image_path = relative / image_file
        print(f'Processing image {relative_image_path}')
        json_file = json_dir / f'{path.name}-{frame}.json'
        if overwrite or not json_file.exists() or dump:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
            success, image = cap.read()
            if success:
                pil_image = Image.fromarray(
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                # pil_image.show()
                if overwrite or not json_file.exists():
                    result = tf_detector.generate_detections_one_image(
                        pil_image, str(relative_image_path))
                    with open(json_file, 'w') as f:
                        json.dump(result, f)
                if dump:
                    pil_image.save(image_dir/image_file)
        frame = frame + pick
    cap.release()


def processPath(path, root, output, image_output, tf_detector, first_frame, last_frame, pick, custom, overwrite, dump):
    if not path.exists():
        print(f'{path} does not exist')
        return
    if path.is_file():
        relative = path.parent.relative_to(root)
    else:
        relative = path.relative_to(root)
    json_dir = output / relative
    image_dir = image_output / relative
    print(f'Output to {json_dir}')
    json_dir.mkdir(parents=True, exist_ok=True)
    if dump:
        image_dir.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        processMedia(path, relative, json_dir, image_dir, tf_detector,
                     first_frame, last_frame, pick, custom, overwrite, dump)
    else:
        for p in path.iterdir():
            if p.is_file():
                processMedia(p, relative, json_dir,  image_dir, tf_detector,
                             first_frame, last_frame, pick, custom, overwrite, dump)
            elif p.is_dir():
                processPath(p, root, output, image_output, tf_detector,
                            first_frame, last_frame, pick, custom, overwrite, dump)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""
Batch processing of media files with megadetector.
""")
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth frame', type=int, default=None)
    parser.add_argument(
        '-c', '--custom', help='custom frame list', type=str, default=None)
    parser.add_argument(
        '--overwrite', help='overwrite existing results', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        '-d', '--dump', help='dump images', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--detector_file', default=getenv('MEGADETECTOR'))
    parser.add_argument(
        '-r', '--root', help='base directory for source files', type=Path, default='data/video')
    parser.add_argument(
        '-o', '--output', help='base directory for detection reports', type=Path, default='data/detection/frames')
    parser.add_argument(
        '-i', '--image_output', help='base directory for dumped images', type=Path, default='data/frames')
    parser.add_argument('media', nargs='+',
                        help='source media folder or file', type=Path)

    args = parser.parse_args()
    if args.custom is not None:
        custom = json.loads(args.custom)
        custom.sort()
    else:
        custom = []
    print(args)
    start_time = time.time()
    print('Loading model:', args.detector_file)
    tf_detector = TFDetector(args.detector_file)
    elapsed = time.time() - start_time
    print('Loaded model (batch level) in {}'.format(
        humanfriendly.format_timespan(elapsed)))

    for path in args.media:
        processPath(path, args.root, args.output,  args.image_output, tf_detector, args.first_frame,
                    args.last_frame, args.pick, custom, args.overwrite, args.dump)
