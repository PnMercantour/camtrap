import psycopg
from psycopg.rows import dict_row
from config import POSTGRES_CONNECTION


def get_id(name):
    return next(x["id"] for x in observation_type if x["application"] == name)


def get_name(id):
    return next(x["application"] for x in observation_type if x["id"] == id)


if __name__ != "__main__":
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
    select * from camtrap.observation_type
                        """
            )
            observation_type = list(cursor)

if __name__ == "__main__":
    import argparse
    from os import getenv
    from pathlib import Path
    from dotenv import load_dotenv

    project_root = Path(__file__).parent.parent.resolve()
    load_dotenv(project_root / ".env")

    parser = argparse.ArgumentParser(description="""Manage Observation types""")

    parser.add_argument(
        "-n",
        "--name",
        help="observation type name",
        type=str,
    )
    parser.add_argument("--id", help="observation type id", type=int)
    parser.add_argument(
        "--pg",
        help="PostgreSQL connection string",
        type=str,
        default=getenv("POSTGRES_CONNECTION"),
    )
    args = parser.parse_args()

    try:
        with psycopg.connect(args.pg, row_factory=dict_row) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
        select * from camtrap.observation_type
                            """
                )
                observation_type = list(cursor)
    except:
        print("database error:", args.pg)
        exit(1)

    if args.name is None and args.id is None:
        print(observation_type)
    elif args.name is not None and args.id is None:
        try:
            print(get_id(args.name))
        except:
            print("observation type not found:", args.name)
            exit(1)
    elif args.id is not None and args.name is None:
        try:
            print(get_name(args.id))
        except:
            print("observation type id not found:", args.id)
            exit(1)
    else:
        print("Provide either name or id to search database")
        print(observation_type)
        exit(1)
