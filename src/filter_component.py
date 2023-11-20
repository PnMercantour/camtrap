import dash_bootstrap_components as dbc
from dash import html, Input
from functools import lru_cache
import psycopg
from psycopg.rows import dict_row
from config import POSTGRES_CONNECTION

cancel_btn = dbc.Button("Abandonner")
commit_btn = dbc.Button("Enregistrer")

filter_fields = [
    "Création d'un filtre",
    cancel_btn,
    commit_btn,
]
component = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row(
                [
                    dbc.Col("Filtres", width="auto"),
                    dbc.Col(add_filter_btn := dbc.Button("+", title="Créer un filtre")),
                ],
                align="center",
                justify="between",
            )
        ),
        dbc.CardBody(
            [
                show_editor := dbc.Collapse(
                    edit := html.Div(filter_fields),
                    is_open=False,
                ),
                filters := dbc.ListGroup(),
                megadetector := dbc.Switch(label="Megadetector", value=True),
            ]
        ),
    ]
)

input = Input(megadetector, "value")


# @lru_cache(maxsize=16)
def metadata(visit_id, megadetector_filter):
    if visit_id is None:
        return []
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            if megadetector_filter:
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
join camtrap.obsmedia on obsmedia.media_id = media.id
join camtrap.observation on observation.id = obsmedia.observation_id
where visit_id=%(visit_id)s
and observation.observation_type_id = 2
and (observation.payload ->> '1')::numeric > 0.4
and coalesce((observation.payload ->> '2')::numeric, 0) < 0.4
and coalesce((observation.payload ->> '3')::numeric, 0) < 0.4
order by media.start_time, file.name
""",
                    {"visit_id": visit_id},
                )
            else:
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
where visit_id=%(visit_id)s
order by media.start_time, file.name
                               """,
                    {"visit_id": visit_id},
                )
            return list(cursor)
