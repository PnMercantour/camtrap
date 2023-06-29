from pathlib import Path
from datetime import datetime
import json
import argparse
import subprocess
import psycopg

from dotenv import load_dotenv
from os import getenv, chdir

exiftoolDateFormat = "%Y:%m:%d %H:%M:%S"

project_root = Path(__file__).parent.parent.resolve()
load_dotenv(project_root / ".env")

MEDIA_ROOT = getenv("MEDIA_ROOT")
POSTGRES_CONNECTION = getenv("POSTGRES_CONNECTION")


def pg_new_project(args):
    with psycopg.connect(args.pg) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
insert into camtrap.project(name, creation_date)
values(%s, %s)
on conflict (name) do update
set update_date = excluded.creation_date
returning id
""",
                (args.project, datetime.now()),
            )
            (id,) = cursor.fetchone()
            return id


def pg_new_file(path, level, parent_id, args):
    with psycopg.connect(args.pg) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
insert into camtrap.file(path, project_id, parent_id, level, creation_date)
values(%s, %s, %s, %s, %s)
on conflict (project_id, path) do update
set (parent_id, level, update_date) = (excluded.parent_id, excluded.level, excluded.creation_date)
returning id
""",
                (str(path), args.project_id, parent_id, level, datetime.now()),
            )
            (id,) = cursor.fetchone()
            return id


def pg_insert_media(exif, relative_path, level, parent_id, args):
    with psycopg.connect(args.pg) as conn:
        with conn.cursor() as cursor:
            for record in exif:
                media_path = record["SourceFile"]
                file_type = record["File:FileType"]
                mime_type = record["File:MIMEType"]
                if file_type == "MP4":
                    start_time = (
                        datetime.strptime(
                            record["QuickTime:CreateDate"], exiftoolDateFormat
                        )
                    ).isoformat()
                    duration = record["QuickTime:Duration"]
                elif file_type == "JPEG":
                    start_time = (
                        datetime.strptime(
                            record["EXIF:DateTimeOriginal"], exiftoolDateFormat
                        )
                    ).isoformat()
                    duration = 0
                else:
                    print(media_path, "ignored: unhandled filetype", file_type)
                    continue
                id = pg_new_file(media_path, level, parent_id, args)

                cursor.execute(
                    """
insert into camtrap.media(
    project_id, id, file_type, mime_type, start_time, duration, creation_date
    ) 
values(%s,%s,%s,%s, %s, %s, %s)
on conflict(id) do update
set (file_type, mime_type, start_time, duration, update_date) = 
(excluded.file_type, excluded.mime_type, excluded.start_time, excluded.duration, excluded.creation_date)
""",
                    (
                        args.project_id,
                        id,
                        file_type,
                        mime_type,
                        start_time,
                        duration,
                        datetime.now(),
                    ),
                )


def processPath(relative_path, level, parent_id, args):
    print("Entering", relative_path, level, parent_id)
    path = args.root / relative_path
    if not path.exists():
        print(f"relative path {relative_path} does not exist")
        return
    if path.is_file():
        print(f"relative path {relative_path} is not a directory")
        return
    else:
        (args.output / relative_path).mkdir(parents=True, exist_ok=True)
        id = pg_new_file(relative_path, level, parent_id, args)
        for p in path.iterdir():
            rel = p.relative_to(args.root)
            if p.is_dir():
                processPath(rel, level + 1, id, args)
        try:
            # https://exiftool.org/exiftool_pod.html
            print("Processing", relative_path)
            sub = subprocess.run(
                [
                    "exiftool",
                    "-fast",
                    "-json",
                    "-groupNames",
                    "--printConv",
                    "--composite",
                    "-ext",
                    "mp4",
                    relative_path,
                ],
                capture_output=True,
                cwd=args.root,
            )
            sub.check_returncode()
            if len(sub.stdout) > 0:
                result = json.loads(sub.stdout)
                if args.insert:
                    pg_insert_media(result, relative_path, level + 1, id, args)
                with (args.output / (relative_path) / "exif.json").open("w") as f:
                    json.dump(result, f)
        except Exception as e:
            print(e)
            print("ERROR: processPath", relative_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Batch processing of media metadata."""
    )
    parser.add_argument(
        "--pg",
        help="PostgreSQL connection string",
        type=str,
        default=POSTGRES_CONNECTION,
    )
    parser.add_argument(
        "--overwrite",
        help="overwrite existing results",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-i",
        "--insert",
        help="insert media into database",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "-r",
        "--root",
        help="base directory for media files",
        type=Path,
        default=MEDIA_ROOT,
    )
    parser.add_argument(
        "-p",
        "--project",
        help="Project name",
        type=str,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="base directory for project data",
        type=Path,
    )
    parser.add_argument("files", nargs="*", help="media folder or file", type=Path)

    args = parser.parse_args()

    args.root = args.root.resolve(strict=True)
    if args.project is None:
        args.project = args.root.name
    if args.output is None:
        args.output = project_root / "data" / args.project / "metadata"
    if args.files == []:
        args.files = [args.root]
    else:
        args.files = [p.resolve(strict=True) for p in args.files]
    args.output.mkdir(parents=True, exist_ok=True)

    args.project_id = pg_new_project(args)
    for path in args.files:
        processPath(path.relative_to(args.root), 0, None, args)
