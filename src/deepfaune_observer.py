import json
import argparse
from pathlib import Path
from os import getenv
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from util import get_project, project_table


project_root = Path(__file__).parent.parent.resolve()
load_dotenv(project_root / ".env")

TOOL = "deepfaune_observer"
APPLICATION = "deepfaune"
MEDIA_ROOT = getenv("MEDIA_ROOT")

PROJECT_TABLE = []


def get_project_id(cursor, name):
    cursor.execute("select id from camtrap.project where name = %s", (name,))
    return list(cursor)[0]["id"]


def add_observation(cursor, payload, media_id, args):
    "creates a deepfaune observation in database, attached to media_id. Don't forget to commit."
    parameters = {
        "application": APPLICATION,
        "project_id": args.project_id,
        "digitizer": f"deepfaune ({args.session_id})",
        "payload": json.dumps(payload),
    }
    if args.dry_run:
        print("add_observation for media", media_id, parameters)
    else:
        cursor.execute(
            """
with observation_type as (select id from camtrap.observation_type where application = %(application)s )
insert into camtrap.observation(project_id, digitizer, observation_type_id, payload) 
select %(project_id)s, %(digitizer)s, observation_type.id, %(payload)s from observation_type
returning id
""",
            parameters,
        )
        observation_id = cursor.fetchone()["id"]
        cursor.execute(
            """
insert into camtrap.obsmedia(observation_id, media_id, ref)
values(%(observation_id)s, %(media_id)s, %(ref)s)
""",
            {
                "observation_id": observation_id,
                "media_id": media_id,
                "ref": None,
            },
        )


def matching_medias(cursor, options={}):
    "returns a list of {media_id, first_frame, last_frame}"
    visit_id = options.get("visit_id", None)
    field_sensor_id = options.get("field_sensor_id", None)
    project_id = options.get("project_id", None)
    if visit_id is not None:
        cursor.execute(
            """
select media_id, min(frame) first_frame, max(frame) last_frame from camtrap.deepfaune join camtrap.media on media.id = media_id
where visit_id = visit_id 
group by media_id
order by media_id""",
        )
    elif field_sensor_id is not None:
        cursor.execute(
            """
select media_id, min(frame) first_frame, max(frame) last_frame from camtrap.deepfaune join camtrap.media on media.id = media_id
where field_sensor_id = %(field_sensor_id)s 
group by media_id
order by media_id""",
            {"field_sensor_id": field_sensor_id},
        )
    elif project_id is not None:
        cursor.execute(
            """
select media_id, min(frame) first_frame, max(frame) last_frame from camtrap.deepfaune join camtrap.media on media.id = media_id
where project_id = %(project_id)s 
group by media_id
order by media_id""",
            {"project_id": project_id},
        )
    else:
        cursor.execute(
            """select media_id, min(frame) first_frame, max(frame) last_frame from camtrap.deepfaune
group by media_id
order by media_id""",
        )
    return list(cursor)


def matching_frames(cursor, media_summary):
    "returns a list of {frame, data}"
    cursor.execute(
        """
select frame, data from camtrap.deepfaune 
where media_id = %(media_id)s and frame between %(first_frame)s and %(last_frame)s
order by frame
""",
        media_summary,
    )
    return list(cursor)


class_list = []


def analyze_frame(detection_data):
    "result contains best confidence score and count for each detected category on this frame"
    aggregator = {}
    for d in detection_data["data"]:
        print("analyze_frame", d)
        c = d["class"]
        c_agg = aggregator.setdefault(c, {"conf": 0, "count": 0})
        c_agg["conf"] = max(c_agg["conf"], d["conf"])
        c_agg["count"] = c_agg["count"] + 1
    return aggregator


def analyze_frames(all_frames):
    "result contains best confidence score and max count for each detected category on this set of frames"
    # result = {}
    # for item in all_frames:
    #     print("item", item)
    #     r = analyze_frame(item["data"])
    #     for c, v in r.items():
    #         result[c] = max(v, result.get(c, 0))
    # return result
    aggregator = {}
    for item in all_frames:
        o = analyze_frame(item)
        for c, v in o.items():
            c_agg = aggregator.setdefault(c, {"conf": 0, "count": 0})
            c_agg["count"] = max(c_agg["count"], v["count"])
            c_agg["conf"] = max(c_agg["conf"], v["conf"])
    return [
        {"class": c, "count": v["count"], "conf": v["conf"]}
        for c, v in aggregator.items()
    ]
    return [analyze_frame(item) for item in all_frames]


def meta2db(cursor, args):
    params = args2json(args)
    cursor.execute(
        """insert into camtrap.session(tool, params)
        values(%(tool)s, %(params)s)
        returning id""",
        {"tool": TOOL, "params": params},
    )
    return cursor.fetchone()["id"]


def run(args):
    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            args.session_id = meta2db(cursor, args=args)
            all_medias = matching_medias(
                cursor, options={"project_id": args.project_id}
            )
            for one_media in all_medias:
                print("processing media:", one_media)
                all_frames = matching_frames(cursor, one_media)
                summary = analyze_frames(all_frames)
                for one_class in summary:
                    add_observation(
                        cursor,
                        one_class,
                        one_media["media_id"],
                        args=args,
                    )
                # if payload:
                #     add_observation(
                #         cursor,
                #         summary,
                #         one_media["media_id"],
                #         args=args,
                #     )
                # for observation in observations:
                #     print(observation)
                #     analyze_frame(observation["data"])


def args2json(args):
    "format args into a valid json string"
    d = dict(vars(args))
    return json.dumps(d)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Synthetize observations from deepfaune raw data."""
    )
    parser.add_argument(
        "-p",
        "--project_name",
        help="Project name",
        type=str,
        default=getenv("PROJECT"),
    )
    parser.add_argument(
        "--pg",
        help="PostgreSQL connection string",
        type=str,
        default=getenv("POSTGRES_CONNECTION"),
    )
    parser.add_argument(
        "-n",
        "--dry_run",
        help="do not write to database",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    args = parser.parse_args()

    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            project = get_project(project_table(cursor), args.project_name)
    if project is None:
        print(f"Error: unknown Project {args.project_name}")
        exit(1)
    args.project_id = project["id"]

    print(
        f"""
Project {args.project_name}
Database: {args.pg}
"""
    )
    run(args)
