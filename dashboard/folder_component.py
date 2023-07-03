import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback_context, callback, no_update, ctx
import dash
import random
import psycopg
from metadata import listSites, listVisits, getVisitMetadata

from config import POSTGRES_CONNECTION


def project_list(cursor):
    print("in project list")
    cursor.execute("select id, name from camtrap.project")
    return [{"label": name, "value": id} for (id, name) in cursor]


def site_list(cursor, project):
    # TEST
    cursor.execute("select id, name from camtrap.site where project_id=%s", (project,))
    return [{"label": name, "value": id} for (id, name) in cursor]


def sensor_list(cursor, project, site):
    cursor.execute(
        "select id, name from camtrap.field_sensor where site_id=%s", (site,)
    )
    return [{"label": name, "value": id} for (id, name) in cursor]


def visit_list(cursor, project, site, sensor):
    # TEST
    cursor.execute(
        "select id, date from camtrap.visit where field_sensor_id=%s order by date desc",
        (sensor,),
    )
    return [{"label": date, "value": id} for (id, date) in cursor]


component = dbc.Card(
    [
        dbc.CardHeader("Sélection"),
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
    print("update selection dropdown", project_value)
    with psycopg.connect(POSTGRES_CONNECTION) as conn:
        print("connected")
        with conn.cursor() as cursor:
            print("cursor")
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
                n_sensor_list = sensor_list(cursor, project_value, site_value)
                n_sensor = None
                n_visit_visible = False
                n_visit_list = []
                n_visit = None
            elif ctx.triggered_id == sensor.id:
                n_visit_list = visit_list(
                    cursor, project_value, site_value, sensor_value
                )
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


input = Input(visit, "value")
