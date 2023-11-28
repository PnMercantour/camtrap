def project_table(cursor):
    cursor.execute("select * from camtrap.project")
    return list(cursor)


def get_project(table, name):
    "returns the attributes for project <name> if this project exists or None"
    for item in table:
        if item["name"] == name:
            return item
    return None
