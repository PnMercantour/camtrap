import json
import argparse
from pathlib import Path
from os import getenv
from dotenv import load_dotenv
import cv2
from PIL import Image
import psycopg
from psycopg.rows import dict_row
from detection.run_detector import load_detector

project_root = Path(__file__).parent.parent.resolve()
load_dotenv(project_root / ".env")


def project_table(cursor):
    cursor.execute("select * from camtrap.project")
    return list(cursor)


def get_project(table, name):
    "returns the attributes for project <name> if this project exists or None"
    for item in table:
        if item["name"] == name:
            return item
    return None


def site_list(cursor, project_id):
    cursor.execute(
        "select id, name from camtrap.site where project_id=%s", (project_id,)
    )
    return list(cursor)


def field_sensor_list(cursor, site_id):
    cursor.execute(
        "select id, name from camtrap.field_sensor where site_id=%s", (site_id,)
    )
    return list(cursor)


def visit_list(cursor, field_sensor):
    cursor.execute(
        "select id, date from camtrap.visit where field_sensor_id=%s order by date desc",
        (field_sensor,),
    )
    return list(cursor)


def media_list(cursor, visit_id):
    """sql result is sorted by start_time then by filename,
    since consecutive still pictures may have the same start_time"""
    if visit_id is None:
        return []
    cursor.execute(
        """
select media.*, file.path
from camtrap.media
join camtrap.file using(id)
where visit_id=%s
order by media.start_time, file.name
""",
        (visit_id,),
    )
    return list(cursor)


def observation_type(cursor, application):
    cursor.execute(
        "select * from camtrap.observation_type where application = %s", (application,)
    )
    return list(cursor)


def meta2db(cursor, args):
    tool = "megadetector_runner"
    params = args2json(args)
    if args.dry_run:
        print("dry run", params)
        return None
    else:
        cursor.execute(
            """insert into camtrap.session(tool, params)
            values(%(tool)s, %(params)s)
            returning id""",
            {"tool": tool, "params": params},
        )
        return cursor.fetchone()["id"]


def store_to_db(cursor, media_id, frame, data, args):
    if args.dry_run:
        print("dry run", media_id, frame, data)
    else:
        cursor.execute(
            """insert into camtrap.megadetector(media_id, frame, session_id, data)
            values(%(media_id)s, %(frame)s, %(session_id)s, %(data)s)""",
            {
                "media_id": media_id,
                "frame": frame,
                "session_id": args.session_id,
                "data": json.dumps(data),
            },
        )


def get_processed_frames(cursor, media_id):
    cursor.execute(
        """select frame from camtrap.megadetector where media_id=%(media_id)s""",
        {"media_id": media_id},
    )
    return [item["frame"] for item in cursor]


def process_media(cursor, media, args):
    media_path = args.root / media["path"]
    if all([not media_path.is_relative_to(f) for f in args.files]):
        return
    print("processing media", media_path)
    processed_frames = get_processed_frames(cursor, media["id"])
    if not media_path.exists():
        print("process_media: path does not exist", media_path)
        return
    if not media_path.is_file():
        print("process_media: not a file", media)
        return
    if media["file_type"] == "MP4":
        cap = cv2.VideoCapture(str(media_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        wish_last_frame = (
            round(fps * args.end_cut)
            if args.end_cut is not None
            else (args.end_frame if args.end_frame is not None else None)
        )
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        first_frame = max(
            0,
            min(args.first_frame, num_frames - 1)
            if args.first_frame is not None
            else 0,
        )
        last_frame = (
            min(num_frames - 1, wish_last_frame)
            if wish_last_frame is not None
            else num_frames - 1
        )
        interval = args.interval
        skip = max(1, int(interval * fps))
        frame = first_frame
        while frame <= last_frame:
            if args.overwrite or (frame not in processed_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                success, image = cap.read()
                if success:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    # pil_image.show()
                    result = args.model.generate_detections_one_image(
                        pil_image,
                        image_id=frame / fps,
                        detection_threshold=args.detection_threshold,
                    )
                    store_to_db(
                        cursor,
                        media["id"],
                        frame,
                        result,
                        args,
                    )
                    print(result)
                    if args.dump:
                        pass
                        # pil_image.save(image_dir / image_file)
                else:
                    print("cap_read failure", media_path, frame)
            frame = frame + skip
        cap.release()
        cursor.execute("commit")
    elif media["file_type"] == "JPEG":
        if args.overwrite or processed_frames != [0]:
            try:
                pil_image = Image.open(media_path)
                result = args.model.generate_detections_one_image(
                    pil_image,
                    image_id=0,
                    detection_threshold=args.detection_threshold,
                )
                store_to_db(
                    cursor,
                    media["id"],
                    0,
                    result,
                    args,
                )
                cursor.execute("commit")
            except:
                print("process_media: invalid image file skipped", media)
    else:
        print("process_media: unhandled media type skipped", media)


def process_visit(cursor, visit, args):
    medias = media_list(cursor, visit["id"])
    for m in medias:
        process_media(
            cursor,
            m,
            args=args,
        )


def process_field_sensor(cursor, field_sensor, args):
    visits = visit_list(cursor, field_sensor["id"])
    for visit in visits:
        process_visit(cursor, visit, args)


def process_site(cursor, site, args):
    field_sensors = field_sensor_list(cursor, site["id"])
    for field_sensor in field_sensors:
        process_field_sensor(cursor, field_sensor, args)


def process_project(cursor, args):
    sites = site_list(cursor, args.project_id)
    for site in sites:
        process_site(cursor, site, args)


def run(args):
    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            args.session_id = meta2db(cursor, args=args)
            args.model = load_detector(str(args.megadetector))
            print("model:", args.model)
            process_project(
                cursor,
                args=args,
            )


def args2json(args):
    d = dict(vars(args))
    d["megadetector"] = str(d["megadetector"])
    d["root"] = str(d["root"])
    d["files"] = [str(f) for f in d["files"]]
    return json.dumps(d)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Raw processing of medias with megadetector."""
    )
    parser.add_argument(
        "-p",
        "--project_name",
        help="Project name",
        type=str,
        default=getenv("PROJECT"),
    )
    parser.add_argument(
        "-md",
        "--megadetector",
        help="megadetector model file",
        type=Path,
        default=getenv("MEGADETECTOR"),
    )
    parser.add_argument(
        "--detection_threshold",
        help="Detection threshold",
        type=float,
        default=getenv("DETECTION_THRESHOLD", 0.2),
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
        "-n",
        "--dry_run",
        help="do not write to database",
        action=argparse.BooleanOptionalAction,
        default=False,
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
        "--first_frame",
        help="first frame to process in video files",
        type=int,
    )
    parser.add_argument(
        "--last_frame",
        help="last frame to process in video files",
        type=int,
    )
    parser.add_argument(
        "-e",
        "--end_cut",
        help="end cut (in seconds) for vidéo files",
        type=float,
    )
    parser.add_argument(
        "--dump",
        help="Dump images to file",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-i",
        "--interval",
        help="sampling interval in seconds for video files",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "files", nargs="*", help="process only these media folders or files", type=Path
    )

    args = parser.parse_args()
    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            project = get_project(project_table(cursor), args.project_name)
    if project is None:
        print(f"Error: unknown Project {args.project_name}")
        exit(1)
    args.project_id = project["id"]

    if args.root is not None:
        root_from = "option --root"
    elif getenv("MEDIA_ROOT") is not None:
        root_from = "MEDIA_ROOT env var"
        args.root = getenv("MEDIA_ROOT")
    elif project.get("root") is not None:
        root_from = "project root attribute in database"
        args.root = project.get("root")
    else:
        print(
            "Error: unspecified root dir: consider updating project table in DB, using --root option, or setting MEDIA_ROOT"
        )
        exit(1)
    try:
        args.root = Path(args.root).resolve(strict=True)
    except:
        print(f"Error: root dir is unreachable: {root_from} was {args.root} ")
        exit(1)
    if args.files == []:
        args.files = [args.root]
    else:
        args.files = [p.resolve(strict=True) for p in args.files]
    args.megadetector = args.megadetector.resolve(strict=True)

    print(
        f"""
Megadetector {args.megadetector}
Project {args.project_name}:{args.project_id}
Media storage root: {args.root}
Database: {args.pg}
"""
    )
    run(args)
