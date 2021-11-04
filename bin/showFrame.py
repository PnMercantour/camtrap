import cv2
from PIL import Image
from pathlib import Path
import argparse


def showFrame(path, output=None, first_frame=0, last_frame=None, pick=None, show=True):
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
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
    frame = first_frame
    while frame <= last_frame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        success, image = cap.read()
        if success:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            if show:
                pil_image.show(title=path.name + '-' + str(frame))
            if output is not None:
                pil_image.save(
                    output / (path.name + '-' + str(frame) + '.jpg'))
        frame = frame + pick
    cap.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='show selected frames from a video file')
    parser.add_argument(
        '-f', '--first_frame', help='first frame', type=int, default=0)
    parser.add_argument('-l', '--last_frame',
                        help='last frame', type=int, default=None)
    parser.add_argument(
        '-p', '--pick', help='pick every nth frame', type=int, default=None)
    parser.add_argument(
        '-o', '--output', help='directory for output files, default to no output', type=Path, default=None)
    parser.add_argument(
        '--show', help='show frames', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('video', nargs='+',
                        help='source video file or folder', type=Path)
    args = parser.parse_args()
    print(args)

    for file in args.video:
        showFrame(file, output=args.output, first_frame=args.first_frame,
                  last_frame=args.last_frame, pick=args.pick, show=args.show)
