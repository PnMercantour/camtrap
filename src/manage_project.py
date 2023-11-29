import argparse
from pathlib import Path
from os import getenv
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from datetime import datetime


def project_table(cursor):
    cursor.execute("select * from camtrap.project")
    return list(cursor)


def create_project(cursor, args):
    if args.project_name is None or args.project_id is not None:
        raise Exception(
            f"Error: create project: wrong arguments : {args.project_name}, {args.project_id}"
        )

    cursor.execute(
        """
insert into camtrap.project(name, root, meta_creation_date)
values(%(project_name)s, %(root)s, %(meta_creation_date)s)
on conflict (name) do update
set meta_update_date = excluded.meta_creation_date,
    root = excluded.root
returning *
""",
        {
            "project_name": args.project_name,
            "root": str(args.root) if args.root is not None else None,
            "meta_creation_date": datetime.now(),
        },
    )
    project = cursor.fetchone()
    cursor.execute("commit")
    return project


def get_project(cursor, args):
    return select_project(project_table(cursor), args)


def update_project(cursor, args):
    cursor.execute(
        """
update camtrap.project
set root = %(root)s,
    meta_update_date = %(meta_update_date)s
where id = %(project_id)s
returning *
""",
        {
            "project_id": args.project_id,
            "root": str(args.root) if args.root is not None else None,
            "meta_update_date": datetime.now(),
        },
    )
    project = cursor.fetchone()
    cursor.execute("commit")
    return project


def delete_project(cursor, args):
    cursor.execute(
        """
delete from camtrap.project
where id = %(project_id)s
returning *
""",
        {"project_id": args.project_id},
    )
    project = cursor.fetchone()
    cursor.execute("commit")
    return project


def select_project(table, args):
    "search for project by name, then by id"
    if args.project_name is not None:
        for item in table:
            if item["name"] == args.project_name:
                if args.project_id is None or item["id"] == args.project_id:
                    return item
                else:
                    raise Exception(
                        f"Error: project name/id mismatch : {args.project_id}, {item}"
                    )
    elif args.project_id:
        for item in table:
            if item["id"] == args.project_id:
                return item
    return None


def registerSession(cursor, tool, params):
    cursor.execute(
        """insert into camtrap.session(tool, params)
        values(%(tool)s, %(params)s)
        returning id""",
        {"tool": tool, "params": params},
    )
    return cursor.fetchone()["id"]


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.resolve()
    load_dotenv(project_root / ".env")

    parser = argparse.ArgumentParser(description="""Manage project in database""")
    parser.add_argument(
        "-p",
        "--project_name",
        help="Project name",
        type=str,
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
        "-c",
        "--create",
        help="Create new project with project name and root, or update an existing project",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-u",
        "--update",
        help="Update root",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "-d",
        "--delete",
        help="Delete project",
        action=argparse.BooleanOptionalAction,
        default=False,
    )

    parser.add_argument(
        "-r",
        "--root",
        help="""Base directory for media files (default: None)""",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    if args.root is not None:
        args.root = args.root.resolve()

    with psycopg.connect(args.pg, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            if args.create:
                project = create_project(cursor, args)
                print("project created or updated")
                print(project)
                exit(0)
            else:
                table = project_table(cursor)
                project = select_project(table, args)
                if project is None:
                    print("---------------")
                    print(f"{len (table)} Projects found in database <{args.pg}>:")
                    print("---------------")
                    for p in table:
                        print("\t", p, "\n")
                    exit(1)
                else:
                    project = select_project(table, args)
                    if args.update:
                        args.project_id = project["id"]
                        project = update_project(cursor, args)
                        print("project updated")
                    elif args.delete:
                        args.project_id = project["id"]
                        project = delete_project(cursor, args)
                        print("project deleted")
                    print(project)
                    exit(0)
