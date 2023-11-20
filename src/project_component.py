"""project_component.py
Project, site, sensor and visit date menus.
"""
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback_context, callback, no_update, ctx
import psycopg
from psycopg.rows import dict_row
from functools import lru_cache
from config import POSTGRES_CONNECTION


def project_list(cursor):
    cursor.execute("select name label, id value  from camtrap.project")
    return list(cursor)


def site_list(cursor, project):
    cursor.execute(
        "select name label, id value from camtrap.site where project_id=%s", (project,)
    )
    return list(cursor)


def sensor_list(cursor, site):
    cursor.execute(
        "select name label, id value from camtrap.field_sensor where site_id=%s",
        (site,),
    )
    return list(cursor)


def visit_list(cursor, sensor):
    cursor.execute(
        "select date label, id value from camtrap.visit where field_sensor_id=%s order by date desc",
        (sensor,),
    )
    return list(cursor)


component = dbc.Card(
    [
        dbc.CardHeader("Projet"),
        dbc.CardBody(
            [
                project := dbc.Select(
                    options=[],
                    placeholder="Choisir un projet",
                ),
                site_visible := dbc.Collapse(
                    site := dbc.Select(
                        options=[],
                        placeholder="Choisir un site",
                    ),
                    is_open=True,
                ),
                sensor_visible := dbc.Collapse(
                    sensor := dbc.Select(
                        options=[],
                        placeholder="Choisir un capteur",
                    ),
                    is_open=False,
                ),
                visit_visible := dbc.Collapse(
                    visit := dbc.Select(
                        options=[],
                        placeholder="Choisir une date de visite",
                    ),
                    is_open=False,
                ),
                cookie := dcc.Store(
                    id="camtrap",
                    storage_type="local",
                ),
            ]
        ),
    ]
)


@callback(
    output=Output(cookie, "data"),
    inputs={
        "project_value": Input(project, "value"),
        "site_value": Input(site, "value"),
        "sensor_value": Input(sensor, "value"),
        "visit_value": Input(visit, "value"),
    },
)
def update_cookie(
    project_value,
    site_value,
    sensor_value,
    visit_value,
):
    "cookie is used to restore project state on page reload"
    return {
        "project": int(project_value) if project_value is not None else None,
        "site": int(site_value) if site_value is not None else None,
        "sensor": int(sensor_value) if sensor_value is not None else None,
        "visit": int(visit_value) if visit_value is not None else None,
    }


@callback(
    output={
        "project": Output(project, "value"),
        "project_list": Output(project, "options"),
        "site_visible": Output(site_visible, "is_open"),
        "site": Output(site, "value"),
        "site_list": Output(site, "options"),
        "sensor_visible": Output(sensor_visible, "is_open"),
        "sensor": Output(sensor, "value"),
        "sensor_list": Output(sensor, "options"),
        "visit_visible": Output(visit_visible, "is_open"),
        "visit": Output(visit, "value"),
        "visit_list": Output(visit, "options"),
    },
    inputs={
        "project_value": Input(project, "value"),
        "site_value": Input(site, "value"),
        "sensor_value": Input(sensor, "value"),
        "visit_value": Input(visit, "value"),
        "cookie_data": State(cookie, "data"),
    },
)
def update_selection_dropdown(
    project_value,
    site_value,
    sensor_value,
    visit_value,
    cookie_data,
):
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            n_project_list = no_update
            n_project = no_update
            n_site_visible = True
            n_site_list = no_update
            n_site = no_update
            n_sensor_visible = True
            n_sensor_list = no_update
            n_sensor = no_update
            n_visit_visible = True
            n_visit_list = no_update
            n_visit = no_update
            if ctx.triggered_id is None:  # init
                try:
                    # parse cookie to restore state ... may fail
                    o_project = int(cookie_data.get("project"))
                    o_site = int(cookie_data.get("site"))
                    o_sensor = int(cookie_data.get("sensor"))
                    o_visit = int(cookie_data.get("visit"))
                except:
                    o_project = None
                n_project_list = project_list(cursor)
                n_project = None
                n_site_visible = False
                n_site_list = []
                n_site = None
                n_sensor_visible = False
                n_sensor_list = []
                n_sensor = None
                n_visit_visible = False
                n_visit_list = []
                n_visit = None
                if any([item["value"] == o_project for item in n_project_list]):
                    # Restore projec_id from cookie
                    n_project = o_project
                    n_site_visible = True
                    n_site_list = site_list(cursor, n_project)
                    if any([item["value"] == o_site for item in n_site_list]):
                        # Restore site_id from cookie
                        n_site = o_site
                        n_sensor_visible = True
                        n_sensor_list = sensor_list(cursor, n_site)
                        if any([item["value"] == o_sensor for item in n_sensor_list]):
                            # Restore sensor_id from cookie
                            n_sensor = o_sensor
                            n_visit_visible = True
                            n_visit_list = visit_list(cursor, n_sensor)
                            if any([item["value"] == o_visit for item in n_visit_list]):
                                # Restore visit_id from cookie
                                n_visit = o_visit
            elif ctx.triggered_id == project.id:
                n_site_list = site_list(cursor, project_value)
                n_site = None
                n_sensor_visible = False
                n_sensor_list = []
                n_sensor = None
                n_visit_visible = False
                n_visit_list = []
                n_visit = None
            elif ctx.triggered_id == site.id:
                n_sensor_list = sensor_list(cursor, site_value)
                n_sensor = None
                n_visit_visible = False
                n_visit_list = []
                n_visit = None
            elif ctx.triggered_id == sensor.id:
                n_visit_list = visit_list(cursor, sensor_value)
                n_visit = None

            return dict(
                project_list=n_project_list,
                project=n_project,
                site_visible=n_site_visible,
                site_list=n_site_list,
                site=n_site,
                sensor_visible=n_sensor_visible,
                sensor_list=n_sensor_list,
                sensor=n_sensor,
                visit_visible=n_visit_visible,
                visit_list=n_visit_list,
                visit=n_visit,
            )


# Public event that can be listened by other modules
input = {"visit_id": Input(visit, "value")}


# @lru_cache(maxsize=16)
def metadata(visit_id):
    "sql result is sorted by start_time then by filename, as consecutive still pictures may have the same start_time"
    if visit_id is None:
        return []
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
select 
    media.id,
    visit_id,
    field_sensor_id,
    file.name, 
    media.mime_type, 
    media.start_time, 
    media.duration, 
    file.path 
from camtrap.media
join camtrap.file using(id)
where visit_id=%s
order by media.start_time, file.name
""",
                (visit_id,),
            )
            return list(cursor)
