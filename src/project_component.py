"""project_component.py
Project, site, sensor and visit date menus.
"""
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, callback_context, callback, no_update, ctx
import psycopg
from psycopg.rows import dict_row
from functools import lru_cache
from config import POSTGRES_CONNECTION
import manage_project
from filter_component import (
    deepfaune_context,
    deepfaune_events,
    apply_deepfaune_filter,
    deepfaune_filter_on,
    refilter,
)

with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
    with conn.cursor() as cursor:
        project_table = manage_project.project_table(cursor)


def project_metadata(project_id):
    for project in project_table:
        if project["id"] == project_id:
            return project


def project_list(cursor):
    cursor.execute("select name label, id value  from camtrap.project")
    return list(cursor)


def site_list(cursor, project):
    cursor.execute(
        "select name label, id value from camtrap.site where project_id=%s", (project,)
    )
    return list(cursor)


def bracket(i):
    return f"[{i}]" if i else ""


def filtered_site_list(cursor, project_id, table, autolock=True):
    if project_id is None:
        return
    project_id = int(project_id)
    p_filtered = refilter(table, "project_id", project_id)
    l = site_list(cursor, project_id)
    for item in l:
        s_filtered = refilter(p_filtered, "site_id", item["value"])
        if autolock:
            item["disabled"] = len(s_filtered) == 0
        count = sum((i["count"] for i in s_filtered))
        item["title"] = f"{count} médias classifiés"
        item["label"] = f'{item["label"]} {bracket(count)}'
    return l


def sensor_list(cursor, site):
    cursor.execute(
        "select name label, id value from camtrap.field_sensor where site_id=%s",
        (site,),
    )
    return list(cursor)


def filtered_sensor_list(cursor, site_id, table, autolock=True):
    if site_id is None:
        return
    site_id = int(site_id)
    s_filtered = refilter(table, "site_id", site_id)
    l = sensor_list(cursor, site_id)
    for item in l:
        fs_filtered = refilter(s_filtered, "field_sensor_id", item["value"])
        if autolock:
            item["disabled"] = len(fs_filtered) == 0
        count = sum((i["count"] for i in fs_filtered))
        item["title"] = f"{count} médias classifiés"
        item["label"] = f'{item["label"]} {bracket(count)}'
    return l


def visit_list(cursor, sensor):
    cursor.execute(
        "select date label, id value from camtrap.visit where field_sensor_id=%s order by date desc",
        (sensor,),
    )
    return list(cursor)


def filtered_visit_list(cursor, field_sensor_id, table, autolock=True):
    if field_sensor_id is None:
        return
    field_sensor_id = int(field_sensor_id)
    fs_filtered = refilter(table, "field_sensor_id", field_sensor_id)
    l = visit_list(cursor, field_sensor_id)
    for item in l:
        v_filtered = refilter(fs_filtered, "visit_id", item["value"])
        if autolock:
            item["disabled"] = len(v_filtered) == 0
        count = sum((i["count"] for i in v_filtered))
        item["title"] = f"{count} médias classifiés"
        item["label"] = f'{item["label"]} {bracket(count)}'
    return l


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
        "deepfaune_context": deepfaune_context,
    },
)
def update_selection_dropdown(
    project_value,
    site_value,
    sensor_value,
    visit_value,
    cookie_data,
    deepfaune_context,
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
                if not deepfaune_filter_on(deepfaune_context):
                    n_site_list = site_list(cursor, project_value)
                else:
                    f_table = apply_deepfaune_filter(deepfaune_context)
                    n_site_list = filtered_site_list(cursor, project_value, f_table)
                n_site = None
                n_sensor_visible = False
                n_sensor_list = []
                n_sensor = None
                n_visit_visible = False
                n_visit_list = []
                n_visit = None
            elif ctx.triggered_id == site.id:
                if not deepfaune_filter_on(deepfaune_context):
                    n_sensor_list = sensor_list(cursor, site_value)
                else:
                    f_table = apply_deepfaune_filter(deepfaune_context)
                    n_sensor_list = filtered_sensor_list(cursor, site_value, f_table)
                n_sensor = None
                n_visit_visible = False
                n_visit_list = []
                n_visit = None
            elif ctx.triggered_id == sensor.id:
                if not deepfaune_filter_on(deepfaune_context):
                    n_visit_list = visit_list(cursor, sensor_value)
                else:
                    f_table = apply_deepfaune_filter(deepfaune_context)
                    n_visit_list = filtered_visit_list(cursor, sensor_value, f_table)
                n_visit = None
            elif ctx.triggered_id in deepfaune_events:
                if deepfaune_filter_on(deepfaune_context):
                    f_table = apply_deepfaune_filter(deepfaune_context)
                    n_site_list = filtered_site_list(cursor, project_value, f_table)
                    n_sensor_list = filtered_sensor_list(cursor, site_value, f_table)
                    n_visit_list = filtered_visit_list(cursor, sensor_value, f_table)
                else:
                    n_site_list = site_list(cursor, project_value)
                    n_sensor_list = sensor_list(cursor, site_value)
                    n_visit_list = visit_list(cursor, sensor_value)
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


# Public events that can be listened to by other modules
input = {"visit_id": Input(visit, "value")}
state = {"visit_id": State(visit, "value")}


@lru_cache(maxsize=8)
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
