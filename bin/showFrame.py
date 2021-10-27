import cv2
from PIL import Image
from pathlib import Path
from argparse import ArgumentParser


def showFrame(path, first_frame, last_frame, pick):
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
    pick = max(pick, 1) if pick else num_frames // 2

    frame = first_frame
    while frame <= last_frame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        success, image = cap.read()
        if success:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_image.show()
        frame = frame + pick


if __name__ == '__main__':
    parser = ArgumentParser(
        description='show selected frames from a video file')
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth frame', type=int, default=10000)
    parser.add_argument('video', nargs='+',
                        help='source video file or folder', type=Path)
    args = parser.parse_args()
    args.first_frame = max(args.first_frame, 0)
    args.pick = max(args.pick, 1)
    print(args)

    for file in args.video:
        showFrame(file, first_frame=args.first_frame,
                  last_frame=args.last_frame, pick=args.pick)
