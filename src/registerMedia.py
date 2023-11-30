from pathlib import Path
from datetime import datetime
import json
import argparse
import subprocess
import psycopg
from psycopg.rows import dict_row

from dotenv import load_dotenv
from os import getenv, chdir

from manage_project import get_project, registerSession

exiftoolDateFormat = "%Y:%m:%d %H:%M:%S"


MEDIA_ROOT = getenv("MEDIA_ROOT")


# def pg_new_project(args):
#     with args.conn.cursor() as cursor:
#         cursor.execute(
#             """
# insert into camtrap.project(name, meta_creation_date)
# values(%s, %s)
# on conflict (name) do update
# set meta_update_date = excluded.meta_creation_date
# returning id
# """,
#             (args.project, datetime.now()),
#         )
#         (id,) = cursor.fetchone()
#         return id


def pg_new_file(path, parent_id, args):
    level = len(path.parts)
    with args.conn.cursor() as cursor:
        cursor.execute(
            """
insert into camtrap.file(path, name, project_id, parent_id, level, meta_creation_date)
values(%s, %s, %s, %s, %s, %s)
on conflict (project_id, path) do update
set (parent_id, name, level, meta_update_date) = 
    (excluded.parent_id, excluded.name, excluded.level, excluded.meta_creation_date)
returning id
""",
            (str(path), path.name, args.project_id, parent_id, level, datetime.now()),
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


def pg_new_media(exif, parent_id, args):
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
                payload = json.dumps(
                    {
                        "frame_rate": record["QuickTime:VideoFrameRate"],
                        "width": record["QuickTime:ImageWidth"],
                        "height": record["QuickTime:ImageHeight"],
                    }
                )
            elif file_type == "JPEG":
                start_time = (
                    datetime.strptime(
                        record["EXIF:DateTimeOriginal"], exiftoolDateFormat
                    )
                ).isoformat()
                duration = 0
                payload = json.dumps(
                    {
                        "width": record["File:ImageWidth"],
                        "height": record["File:ImageHeight"],
                    }
                )
            else:
                print(media_path, "ignored: unhandled filetype", file_type)
                continue
            id = pg_new_file(media_path, parent_id, args)

            cursor.execute(
                """
insert into camtrap.media(
    project_id, id, file_type, mime_type, start_time, duration, meta_creation_date, payload
    ) 
values(%s,%s,%s,%s, %s, %s, %s, %s)
on conflict(id) do update
set (file_type, mime_type, start_time, duration, meta_update_date, payload) = 
(excluded.file_type, excluded.mime_type, excluded.start_time, excluded.duration, excluded.meta_creation_date, excluded.payload)
""",
                (
                    args.project_id,
                    id,
                    file_type,
                    mime_type,
                    start_time,
                    duration,
                    datetime.now(),
                    payload,
                ),
            )


def processPath(relative_path, parent_id, args):
    print("Entering", relative_path)
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
                    "-ext",
                    "jpg",
                    relative_path,
                ],
                capture_output=True,
                cwd=args.root,
            )
            sub.check_returncode()
            if len(sub.stdout) > 0:
                exif = json.loads(sub.stdout)
                if args.insert:
                    pg_new_media(exif, id, args)
                with (args.output / (relative_path) / "exif.json").open("w") as f:
                    json.dump(exif, f)
        except Exception as e:
            print(e)
            print("ERROR: processPath", relative_path)
            raise


def run(args):
    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            args.session_id = registerSession(cursor, "registerMedia", args2json(args))

    with psycopg.connect(args.pg) as conn:
        args.conn = conn
        for path in args.files:
            relative_path = path.relative_to(args.root)
            parent_id = pg_file_chain(relative_path, args)
            processPath(relative_path, parent_id, args)


def args2json(args):
    d = dict(vars(args))
    d["root"] = str(d["root"])
    d["output"] = str(d["output"])
    d["files"] = [str(f) for f in d["files"]]
    print(d)
    return json.dumps(d)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.resolve()
    load_dotenv(project_root / ".env")

    parser = argparse.ArgumentParser(
        description="""Register Media files into database"""
    )
    parser.add_argument(
        "-p",
        "--project_name",
        help="Project name",
        type=str,
        # default=getenv("PROJECT"),
    )
    parser.add_argument(
        "-id",
        "--project_id",
        help="Project id",
        type=int,
    )

    parser.add_argument(
        "--pg",
        help="PostgreSQL connection string",
        type=str,
        default=getenv("POSTGRES_CONNECTION"),
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
        help="""base directory for media files, 
    defaults to MEDIA_ROOT env variable (if defined)
    or to the root attribute of the project table in the database""",
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="base directory for project data",
        type=Path,
    )
    parser.add_argument("files", nargs="*", help="media folder or file", type=Path)

    args = parser.parse_args()

    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            project = get_project(cursor, args)
            if project is None:
                print("Project not found", args.project_name, args.project_id)
                exit(1)
            args.project_name = project["name"]
            args.project_id = project["id"]
            if args.root is None:
                if project["root"] is None:
                    print("Unspecified Base directory for media files")
                    exit(1)
                args.root = Path(project["root"])
            try:
                args.root = Path(args.root).resolve(strict=True)
            except:
                print(f"unreachable Base directory: {args.root}")
                exit(1)
            print(args)
            if args.output is None:
                args.output = project_root / "data" / args.project_name / "metadata"
            if args.files == []:
                args.files = [args.root]
            else:
                args.files = [p.resolve(strict=True) for p in args.files]
            args.output.mkdir(parents=True, exist_ok=True)
            print(
                f"""
        Project {args.project_name}
        Media storage root: {args.root}
        Database: {args.pg}
        """
            )
    run(args)
