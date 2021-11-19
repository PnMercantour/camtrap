from pathlib import Path
from datetime import datetime
import json
import cv2 as cv
import argparse


def decode_fourcc(cc):
    return "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])


def videoMetadata(path, root=Path()):
    # TODO : retrieve the creation date from exif data.
    # https://exiftool.org/TagNames/QuickTime.html
    # exiftool -MediaCreateDate -MediaDuration -j -r <DIR>
    stat = path.stat()
    cap = cv.VideoCapture(str(path))
    attr = dict(path=str(path.relative_to(root)), size=stat.st_size, timestamp=stat.st_mtime,
                date=str(datetime.fromtimestamp(stat.st_mtime)),
                codec=decode_fourcc(cap.get(cv.CAP_PROP_FOURCC)),
                fps=cap.get(cv.CAP_PROP_FPS),
                frame_width=int(cap.get(cv.CAP_PROP_FRAME_WIDTH)),
                frame_height=int(cap.get(cv.CAP_PROP_FRAME_HEIGHT)),
                frame_count=int(cap.get(cv.CAP_PROP_FRAME_COUNT)))
    cap.release()
    return attr
# print(videoMetadata(Path('data/video/test/IMG_0006.MP4'), Path('data/video')))


def processVideo(path, root, attr_dir, overwrite=False):
    if not path.is_file():
        print(path, 'not a file')
        return
    if path.suffix not in ['.MP4', '.mp4']:
        print(path, 'unknown suffix')
        return
    print(f'Processing video {path}')

    attr_file = attr_dir / f'{path.name}.json'
    if overwrite or not attr_file.exists():
        attr = videoMetadata(path, root)
        with open(attr_file, 'w') as f:
            json.dump(attr, f, indent=1)


def processPath(path, root, output, overwrite):
    if not path.exists():
        print(f'{path} does not exist')
        return
    if path.is_file():
        relative = path.parent.relative_to(root)
    else:
        relative = path.relative_to(root)
    attr_dir = output / relative
    print(f'Output to {attr_dir}')
    attr_dir.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        processVideo(path, root, attr_dir, overwrite)
    else:
        for p in path.iterdir():
            if p.is_file():
                processVideo(p, root,  attr_dir,  overwrite)
            if p.is_dir():
                processPath(p, root, output,  overwrite)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Batch processor to store video metadata.""")
    parser.add_argument(
        '--overwrite', help='overwrite existing results', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        '-r', '--root', help='base directory for source files', type=Path, default='data/video')
    parser.add_argument(
        '-o', '--output', help='base directory for video metadata', type=Path, default='data/video_metadata')
    parser.add_argument('video', nargs='+',
                        help='source video folder or file', type=Path)

    args = parser.parse_args()
    print(args)

    for path in args.video:
        processPath(path, args.root, args.output, args.overwrite)
