import cv2
import argparse
from os import getenv
from dotenv import load_dotenv
import json
import numpy as np
from pathlib import Path
from PIL import Image

import torch
from torch import tensor
from torchvision.transforms import InterpolationMode, transforms
import psycopg
from psycopg.rows import dict_row

from detectTools import cropSquare
from classifTools import Model, CROP_SIZE, txt_animalclasses

BATCH_SIZE = 1


def project_table(cursor):
    cursor.execute("select * from camtrap.project")
    return list(cursor)


def get_project(table, name):
    "returns the attributes for project <name> if this project exists or None"
    for item in table:
        if item["name"] == name:
            return item
    return None


def meta2db(cursor, args):
    tool = "deepfaune_runner"
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
        print("dry run store to db", media_id, frame, data)
    elif args.overwrite:
        cursor.execute(
            """
insert into camtrap.deepfaune(media_id, frame, session_id, data)
values(%(media_id)s, %(frame)s, %(session_id)s, %(data)s)
on conflict(media_id, frame) do update
set session_id = excluded.session_id,
    data = excluded.data
""",
            {
                "media_id": media_id,
                "frame": frame,
                "session_id": args.session_id,
                "data": json.dumps(data),
            },
        )
    else:
        cursor.execute(
            """insert into camtrap.deepfaune(media_id, frame, session_id, data)
            values(%(media_id)s, %(frame)s, %(session_id)s, %(data)s)""",
            {
                "media_id": media_id,
                "frame": frame,
                "session_id": args.session_id,
                "data": json.dumps(data),
            },
        )


def get_megadetector_data(cursor, media_id):
    cursor.execute(
        """select frame, data from camtrap.megadetector where media_id=%(media_id)s
        order by frame""",
        {"media_id": media_id},
    )
    return list(cursor)


def get_processed_frames(cursor, media_id):
    cursor.execute(
        """select frame from camtrap.deepfaune where media_id=%(media_id)s""",
        {"media_id": media_id},
    )
    return [item["frame"] for item in cursor]


class Classifier:
    # Adapted from deepfaune Classifier

    def __init__(self, args):
        self.model = Model()
        self.model.loadWeights(str(args.deepfaune))
        self.transforms = transforms.Compose(
            [
                transforms.Resize(
                    size=(CROP_SIZE, CROP_SIZE),
                    interpolation=InterpolationMode.BICUBIC,
                    max_size=None,
                    antialias=None,
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=tensor([0.4850, 0.4560, 0.4060]),
                    std=tensor([0.2290, 0.2240, 0.2250]),
                ),
            ]
        )

    def predictOnBatch(self, batchtensor):
        return self.model.predict(batchtensor)

    # croppedimage loaded by PIL
    def preprocessImage(self, croppedimage):
        preprocessimage = self.transforms(croppedimage)
        return preprocessimage.unsqueeze(dim=0)


def process_detection(pil_image, detection, args):
    box = detection["bbox"]
    xmin = int(box[0] * pil_image.width)
    ymin = int(box[1] * pil_image.height)
    xmax = xmin + int(box[2] * pil_image.width)
    ymax = ymin + int(box[3] * pil_image.height)
    cropbox = [xmin, ymin, xmax, ymax]
    croppedimage = cropSquare(pil_image, cropbox)
    t_image = args.classifier.preprocessImage(croppedimage)
    # cropped_data = torch.ones((BATCH_SIZE, 3, CROP_SIZE, CROP_SIZE))
    prediction = args.classifier.predictOnBatch(t_image)
    the_class = np.argmax(prediction[0]).item()
    the_conf = round(np.max(prediction[0]).item(), 3)
    the_species = txt_animalclasses["fr"][the_class]
    return {
        "bbox": box,
        "conf": the_conf,
        "class": the_class,
        "species": the_species,
    }


def process_image(pil_image, detections, args):
    # Process an image (or video frame)
    # Returns a list of objects [{<bbox>, <conf>, <class>, <species>}*]
    # prefer using class than species which is provided only to improve readability
    return [
        process_detection(pil_image, detection, args)
        for detection in detections
        if detection["category"] == "1" and detection["conf"] >= 0.4
    ]
    result = []
    for subindex, detection in enumerate(detections):
        if detection["category"] != "1":
            # do not process Human or vehicle detections
            continue
        if detection["conf"] < 0.4:
            continue
        box = detection["bbox"]
        xmin = int(box[0] * pil_image.width)
        ymin = int(box[1] * pil_image.height)
        xmax = xmin + int(box[2] * pil_image.width)
        ymax = ymin + int(box[3] * pil_image.height)
        cropbox = [xmin, ymin, xmax, ymax]
        croppedimage = cropSquare(pil_image, cropbox)
        t_image = args.classifier.preprocessImage(croppedimage)
        # cropped_data = torch.ones((BATCH_SIZE, 3, CROP_SIZE, CROP_SIZE))
        prediction = args.classifier.predictOnBatch(t_image)
        the_class = np.argmax(prediction[0]).item()
        the_conf = np.max(prediction[0]).item()
        the_species = txt_animalclasses["fr"][the_class]
        result.append(
            {
                "bbox": box,
                "conf": the_conf,
                "class": the_class,
                "species": the_species,
            }
        )
    return result


def process_media(cursor, media, args):
    media_path = args.root / media["path"]
    if all([not media_path.is_relative_to(f) for f in args.files]):
        return
    print("processing media", media)
    megadetector_data = get_megadetector_data(cursor, media["id"])
    processed_frames = get_processed_frames(cursor, media["id"])
    if not media_path.exists():
        print("process_media: path does not exist", media_path)
        return
    if not media_path.is_file():
        print("process_media: not a file", media)
        return
    if media["file_type"] == "MP4":
        # Lazy loading of video file
        cap = None
        for item in megadetector_data:
            print(item)
            frame = item["frame"]
            if (args.overwrite or not frame in processed_frames) and frame in [
                0,
                15,
                20,
                30,
                40,
                45,
                60,
                120,
                240,
            ]:
                cap = cap if cap is not None else cv2.VideoCapture(str(media_path))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                success, image = cap.read()
                if success:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    store_to_db(
                        cursor,
                        media["id"],
                        frame,
                        process_image(pil_image, item["data"]["detections"], args),
                        args,
                    )
        if cap:
            cap.release()
            cursor.execute("commit")
    elif media["file_type"] == "JPEG":
        if args.overwrite or processed_frames != [0]:
            try:
                pil_image = Image.open(media_path)
                for item in megadetector_data:
                    # expect only one item, for frame #0
                    frame = item["frame"]
                    store_to_db(
                        cursor,
                        media["id"],
                        frame,
                        process_image(pil_image, item["data"]["detections"], args),
                        args,
                    )
                # detections = media["data"]["detections"]
                # result = []
                # for subindex, detection in enumerate(detections):
                #     if detection["category"] != "1":
                #         print("not an animal", detection)
                #         continue
                #     if detection["conf"] < 0.4:
                #         print("under threshold", detection)
                #         continue
                #     box = detection["bbox"]
                #     xmin = int(box[0] * pil_image.width)
                #     ymin = int(box[1] * pil_image.height)
                #     xmax = xmin + int(box[2] * pil_image.width)
                #     ymax = ymin + int(box[3] * pil_image.height)
                #     cropbox = [xmin, ymin, xmax, ymax]
                #     croppedimage = cropSquare(pil_image, cropbox)
                #     t_image = args.classifier.preprocessImage(croppedimage)
                #     # cropped_data = torch.ones((BATCH_SIZE, 3, CROP_SIZE, CROP_SIZE))
                #     prediction = args.classifier.predictOnBatch(t_image)
                #     print("prediction")
                #     # print(prediction)
                #     # print(prediction[0])
                #     # print(np.argmax(prediction[0]))
                #     the_class = np.argmax(prediction[0])
                #     the_conf = np.max(prediction[0])
                #     the_species = txt_animalclasses["fr"][the_class]
                #     result.append(
                #         {
                #             "bbox": box,
                #             "conf": the_conf,
                #             "class": "the_class",
                #             "species": the_species,
                #         }
                #     )
                #     # print(txt_animalclasses["fr"][np.argmax(prediction[0])])
                #     # result.append({"bbox": box, "species": "prediction": prediction.tolist()})
                # store_to_db(
                #     cursor,
                #     media["id"],
                #     0,
                #     process_image(pil_image, item["data"]["detections"]),
                #     args,
                # )
                cursor.execute("commit")
            except:
                print("process_media: invalid image skipped", media)
                raise
    else:
        print("process_media: unhandled media type skipped", media)


def process_project(cursor, args):
    cursor.execute(
        """
select 
    media.id, 
    media.file_type, 
    file.path
from camtrap.media 
join camtrap.file on media.id = file.id
where file.project_id = %(project_id)s
                       """,
        {"project_id": args.project_id},
    )
    records = list(cursor)
    # all megadetector records for project, with additional file info.
    # cursor can be reused by internal functions.
    for media in records:
        process_media(cursor, media, args)


def run(args):
    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            args.session_id = meta2db(cursor, args=args)
            args.classifier = Classifier(args)
            process_project(
                cursor,
                args=args,
            )


def args2json(args):
    d = dict(vars(args))
    d["deepfaune"] = str(d["deepfaune"])
    d["root"] = str(d["root"])
    d["files"] = [str(f) for f in d["files"]]
    return json.dumps(d)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.resolve()
    load_dotenv(project_root / ".env")

    parser = argparse.ArgumentParser(
        description="""Media classification with deepfaune"""
    )
    parser.add_argument(
        "-p",
        "--project_name",
        help="Project name",
        type=str,
        default=getenv("PROJECT"),
    )
    parser.add_argument(
        "--deepfaune",
        help="deepfaune classification model",
        type=Path,
        default=getenv("DEEPFAUNE_MODEL"),
    )
    # parser.add_argument(
    #     "-md",
    #     "--megadetector",
    #     help="megadetector model file",
    #     type=Path,
    #     default=getenv("MEGADETECTOR"),
    # )
    # parser.add_argument(
    #     "--detection_threshold",
    #     help="Detection threshold",
    #     type=float,
    #     default=getenv("DETECTION_THRESHOLD", 0.2),
    # )
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
    # parser.add_argument(
    #     "--first_frame",
    #     help="first frame to process in video files",
    #     type=int,
    # )
    # parser.add_argument(
    #     "--last_frame",
    #     help="last frame to process in video files",
    #     type=int,
    # )
    # parser.add_argument(
    #     "-e",
    #     "--end_cut",
    #     help="end cut (in seconds) for vidéo files",
    #     type=float,
    # )
    parser.add_argument(
        "--dump",
        help="Dump images to file",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    # parser.add_argument(
    #     "-i",
    #     "--interval",
    #     help="sampling interval in seconds for video files",
    #     type=float,
    #     default=1.0,
    # )
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
    args.deepfaune = args.deepfaune.resolve(strict=True)

    print(
        f"""
Model {args.deepfaune}
Project {args.project_name}:{args.project_id}
Media storage root: {args.root}
Database: {args.pg}
"""
    )
    run(args)
