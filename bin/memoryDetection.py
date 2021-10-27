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
            #pil_image.show()
            result = tf_detector.generate_detections_one_image(
                pil_image, frame)
            print(result)
            detection_results.append(result)
        frame = frame + pick
    return detection_results


if __name__ == '__main__':
    parser = ArgumentParser(
        description='get selected frames from a video file')
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth sample', type=int, default=6)
    parser.add_argument(
        '-d', '--dest_dir', help='destination directory', type=Path)
    parser.add_argument('--detector_file', default=getenv('MEGADETECTOR'))
    parser.add_argument(
        '--ncores',
        type=int,
        default=0,
        help='Number of cores to use; only applies to CPU-based inference, does not support checkpointing when ncores > 1')
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.1,
        help="Confidence threshold between 0 and 1.0, don't include boxes below this confidence in the output file. Default is 0.1")
    parser.add_argument('video', nargs='+',
                        help='source video file or folder', type=Path)
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
        # results = md.process_images(
        #     img_files, tf_detector, confidence_threshold=0.1)

        # results = md.load_and_run_detector_batch(model_file=args.detector_file,
        #                                          image_file_names=[
        #                                              'frames/IMG_0006-0.jpg', 'frames/IMG_0006-360.jpg'],
        #                                          checkpoint_path=None,
        #                                          confidence_threshold=args.threshold,
        #                                          # checkpoint_frequency=args.checkpoint_frequency,
        #                                          # results=results,
        #                                          n_cores=args.ncores)
