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
    with args.conn.cursor() as cursor:
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


def pg_new_file(path, parent_id, args):
    level = len(path.parts)
    with args.conn.cursor() as cursor:
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


def pg_file_chain(path, args):
    """
    ensure that path parents are all created in pg up to root
    Return <id> of parent file"""
    if len(path.parts) == 0:
        return None
    else:
        grand_parent_id = pg_file_chain(path.parent, args)
        return pg_new_file(path.parent, grand_parent_id, args)


def pg_insert_media(exif, parent_id, args):
    with args.conn.cursor() as cursor:
        for record in exif:
            media_path = Path(record["SourceFile"])
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
            id = pg_new_file(media_path, parent_id, args)

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


def processPath(relative_path, parent_id, args):
    print("Entering", relative_path, parent_id)
    path = args.root / relative_path
    if not path.exists():
        print(f"relative path {relative_path} does not exist")
        return
    if path.is_file():
        print(f"relative path {relative_path} is not a directory")
        return
    else:
        (args.output / relative_path).mkdir(parents=True, exist_ok=True)
        id = pg_new_file(relative_path, parent_id, args)
        for p in path.iterdir():
            rel = p.relative_to(args.root)
            if p.is_dir():
                processPath(rel, id, args)
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
                exif = json.loads(sub.stdout)
                if args.insert:
                    pg_insert_media(exif, id, args)
                with (args.output / (relative_path) / "exif.json").open("w") as f:
                    json.dump(exif, f)
        except Exception as e:
            print(e)
            print("ERROR: processPath", relative_path)
            raise


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
    with psycopg.connect(args.pg) as conn:
        args.conn = conn
        args.project_id = pg_new_project(args)
        for path in args.files:
            relative_path = path.relative_to(args.root)
            parent_id = pg_file_chain(relative_path, args)
            processPath(relative_path, parent_id, args)
