from dash import (
    html,
    callback,
    Output,
    Input,
    State,
    no_update,
)
import dash_bootstrap_components as dbc
import psycopg
from psycopg.rows import dict_row
from config import POSTGRES_CONNECTION
import project_component

component = html.Div(
    children=[
        dbc.Card(
            [
                dbc.CardHeader("Statistiques de la visite"),
                dbc.CardBody(data := html.Div()),
            ]
        )
    ]
)


@callback(
    output=Output(data, "children"),
    inputs={
        "active_tab": Input("tabs", "active_tab"),
        "project_id": Input(project_component.project, "value"),
        "visit_id": Input(project_component.visit, "value"),
    },
)
def update(visit_id, project_id, active_tab):
    if active_tab != "stat_visit":
        return no_update
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
select count(*) count from camtrap.media where visit_id = %(visit_id)s
                           """,
                {"visit_id": visit_id},
            )
            result = cursor.fetchone()
    return active_tab + f"  {visit_id}  {result} {project_id} {type(project_id)}"
