import cv2
from PIL import Image
from os import getenv
import time
from pathlib import Path
import humanfriendly
from argparse import ArgumentParser
from detection.run_tf_detector import TFDetector
from detection import run_tf_detector_batch as md


def processVideo(path, tf_detector, first_frame, last_frame, pick):
    """process <path> video file with <tf_detector>
    invokes tf_detector.generate_detections_one_image on all selected frames
    returns the list of results"""
    if not path.is_file():
        print(path, 'not a file')
        return
    print('processing', path)
    cap = cv2.VideoCapture(str(path))
    num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    first_frame = max(0, min(first_frame, num_frames - 1)
                      ) if first_frame is not None else 0
    last_frame = min(
        num_frames - 1, last_frame) if last_frame else num_frames - 1
    pick = max(pick, 1) if pick else 1

    frame = first_frame
    detection_results = []
    while frame <= last_frame:
        print('frame', frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        success, image = cap.read()
        if success:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            # pil_image.show()
            result = tf_detector.generate_detections_one_image(
                pil_image, frame)
            # print(result)
            detection_results.append(result)
        frame = frame + pick
    return detection_results


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Analyse selected frames from a video file. Print results on stdout')
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth sample', type=int, default=6)
    parser.add_argument('--detector_file', default=getenv('MEGADETECTOR'))
    parser.add_argument('video', nargs='+',
                        help='source video files', type=Path)
    args = parser.parse_args()
    args.first_frame = max(args.first_frame, 0)
    args.pick = max(args.pick, 1)
    print(args)
    start_time = time.time()
    print('Loading model:', args.detector_file)
    tf_detector = TFDetector(args.detector_file)
    elapsed = time.time() - start_time
    print('Loaded model (batch level) in {}'.format(
        humanfriendly.format_timespan(elapsed)))

    for file in args.video:
        results = processVideo(file,  tf_detector, first_frame=args.first_frame,
                               last_frame=args.last_frame, pick=args.pick)
        print(results)
