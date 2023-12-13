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
from util import txt_animalclasses


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
    #     with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
    #         with conn.cursor() as cursor:
    #             cursor.execute(
    #                 """
    # select count(*) count from camtrap.media where visit_id = %(visit_id)s
    #                            """,
    #                 {"visit_id": visit_id},
    #             )
    #             result = cursor.fetchone()
    #     return active_tab + f"  {visit_id}  {result} {project_id} {type(project_id)}"
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
select path, class, count(*) from camtrap.deepfaune_synthesis s 
join camtrap.file on (s.visit_id = file.id)
where conf > 0.5
group by path, class
order by path, class
                           """
            )
            result = [
                f'{ i["path"]}: {txt_animalclasses["fr"][i["class"]]} ({i["count"]})'
                for i in cursor
            ]
            print(result)
            return result
