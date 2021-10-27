import cv2
from PIL import Image
from os import getenv
import time
import json
from pathlib import Path
import humanfriendly
from argparse import ArgumentParser
from detection.run_tf_detector import TFDetector
from detection import run_tf_detector_batch as md


def processVideo(path, out_dir, empty_dir, other_dir, data_dir, tf_detector, first_frame, last_frame, pick):
    if not path.is_file():
        print(path, 'not a file')
        return
    print('processing', path)
    if path.suffix != '.MP4':
        print(path, 'unknwon suffix')
        return
    cap = cv2.VideoCapture(str(path))
    num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    first_frame = max(0, min(first_frame, num_frames - 1)
                      ) if first_frame is not None else 0
    last_frame = min(
        num_frames - 1, last_frame) if last_frame else num_frames - 1
    pick = max(pick, 1) if pick else 1

    frame = first_frame
    animal_count = 0
    other_count = 0
    while frame <= last_frame:
        print('Processing', path, frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        success, image = cap.read()
        if success:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            # pil_image.show()
            result = tf_detector.generate_detections_one_image(
                pil_image, frame)
            print(result)
            with open(data_dir / (path.name + '-'+str(frame) + '.json'), 'w') as f:
                json.dump(result, f, indent=1)
            for detection in result["detections"]:
                if detection["category"] == '1':
                    animal_count = animal_count + 1
                else:
                    other_count = other_count + 1
                print('detection', detection, animal_count, other_count)
        frame = frame + pick
    for dir in [out_dir, empty_dir, other_dir]:
        link = (dir / path.name)
        if link.is_symlink():
            link.unlink()
    if other_count == 0:
        if animal_count == 0:
            target_dir = empty_dir
        else:
            target_dir = out_dir
    else:
        target_dir = other_dir
    (target_dir / path.name).symlink_to(path.resolve())
    print(target_dir / path.name, animal_count, other_count)


def processDirectory(dir, root, output, tf_detector, first_frame, last_frame, pick):
    relative = dir.relative_to(root)
    out_dir = output / relative
    out_dir.mkdir(parents=True, exist_ok=True)
    empty_dir = (out_dir / ".empty")
    empty_dir.mkdir(exist_ok=True)
    other_dir = (out_dir / ".other")
    other_dir.mkdir(exist_ok=True)
    data_dir = out_dir / '.MD_Data'
    data_dir.mkdir(exist_ok=True)
    for path in dir.iterdir():
        processVideo(path, out_dir, empty_dir, other_dir, data_dir,
                     tf_detector, first_frame, last_frame, pick)


if __name__ == '__main__':
    parser = ArgumentParser(
        description='get selected frames from a video file')
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth frame', type=int, default=6)

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

    parser.add_argument(
        '-r', '--root', help='root directory for source files', type=Path, default='')
    parser.add_argument(
        '-o', '--output', help='output directory', type=Path, default='MD output')
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

    for path in args.video:
        results = processDirectory(path, args.root, args.output,  tf_detector, first_frame=args.first_frame,
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
