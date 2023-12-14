import dash_bootstrap_components as dbc
from dash import html, Input, dcc
from functools import lru_cache
import psycopg
from psycopg.rows import dict_row
from config import POSTGRES_CONNECTION
import observation_type
from util import txt_animalclasses

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
                    # dbc.Col(add_filter_btn := dbc.Button("+", title="Créer un filtre")),
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
                megadetector_switch := dbc.Switch(label="Megadetector", value=True),
                dbc.Label("Seuil de détection"),
                megadetector_threshold := dcc.Slider(
                    min=0,
                    max=1,
                    step=0.02,
                    marks=None,
                    value=0.4,
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Hr(),
                deepfaune_switch := dbc.Switch(label="DeepFaune", value=True),
                deepfaune_select := dbc.Select(
                    options=[{"label": "Tout afficher", "value": "all"}]
                    + [
                        {"label": v, "value": k}
                        for k, v in enumerate(txt_animalclasses["fr"])
                    ],
                    placeholder="Choisir une espèce",
                    value="all",
                ),
                dbc.Label("Seuil de détection"),
                deepfaune_threshold := dcc.Slider(
                    min=0,
                    max=1,
                    step=0.02,
                    marks=None,
                    value=0.5,
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
    ]
)

input = Input(megadetector_switch, "value")

# megadetector_context = {
#     "active": Input(megadetector_switch, "value"),
#     "threshold": Input(megadetector_threshold, "value"),
# }
megadetector_context = (
    Input(megadetector_switch, "value"),
    Input(megadetector_threshold, "value"),
)

megadetector_events = [
    megadetector_switch.id,
    megadetector_threshold.id,
]

# deepfaune_context = {
#     "active": Input(deepfaune_switch, "value"),
#     "threshold": Input(deepfaune_threshold, "value"),
#     "selection": Input(deepfaune_select, "value"),
# }

deepfaune_context = (
    Input(deepfaune_switch, "value"),
    Input(deepfaune_threshold, "value"),
    Input(deepfaune_select, "value"),
)

deepfaune_events = [deepfaune_switch.id, deepfaune_threshold.id, deepfaune_select.id]

# context = {
#     "megadetector": megadetector_context,
#     "deepfaune": deepfaune_context,
# }

context = (megadetector_context, deepfaune_context)

events = megadetector_events + deepfaune_events


def pack_context(context):
    "Fix to dash using lists instead of tuples"
    return tuple((tuple(i) for i in context))


def deepfaune_filter_on(context):
    (active, threshold, selection) = context
    return active and selection != "all"


def apply_deepfaune_filter(context):
    return _apply_deepfaune_filter(tuple(context))


@lru_cache(maxsize=4)
def _apply_deepfaune_filter(context):
    (active, threshold, selection) = context
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
select s.visit_id, s.field_sensor_id, fs2.site_id, s.project_id, count(*) 
from camtrap.deepfaune_synthesis s join camtrap.field_sensor fs2 on field_sensor_id = fs2.id 
where class = %(class)s and conf >= %(conf)s
group by s.visit_id, s.field_sensor_id, fs2.site_id, s.project_id
""",
                {"class": selection, "conf": threshold},
            )
            return list(cursor)


def refilter(data, key, value):
    return [item for item in data if item[key] == value]


def metadata(visit_id, filter_context):
    if visit_id is None:
        return []
    return _metadata(visit_id, pack_context(filter_context))


@lru_cache(maxsize=8)
def _metadata(visit_id, filter_context):
    # all args must be immutable
    if visit_id is None:
        return []
    (
        (megadetector_active, megadetector_threshold),
        (deepfaune_active, deepfaune_threshold, deepfaune_selection),
    ) = filter_context

    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            # ----------------------------------
            if megadetector_active and not deepfaune_active:
                print("seulement megadetector")
                cursor.execute(
                    """
select 
    media.id media_id,
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
and observation.observation_type_id = %(observation_type_id)s
and (observation.payload ->> '1')::numeric >= %(megadetector_threshold)s
and coalesce((observation.payload ->> '2')::numeric, 0) <= %(megadetector_threshold)s
and coalesce((observation.payload ->> '3')::numeric, 0) <= %(megadetector_threshold)s
order by media.start_time, file.name
""",
                    {
                        "visit_id": visit_id,
                        "megadetector_threshold": megadetector_threshold,
                        "observation_type_id": observation_type.get_id("megadetector"),
                    },
                )
            # ----------------------------------
            elif (
                megadetector_active
                and deepfaune_active
                and deepfaune_selection != "all"
            ):
                print(
                    "megadetector et deepfaune",
                    visit_id,
                )
                cursor.execute(
                    """

select distinct on(start_time, file.name) 
    s.media_id,
    s.visit_id,
    s.field_sensor_id,
    file.name, 
    s.mime_type, 
    s.start_time, 
    s.duration, 
    file.path 
from camtrap.deepfaune_synthesis s
join camtrap.file on s.media_id = file.id
join camtrap.obsmedia on obsmedia.media_id = s.media_id
join camtrap.observation on observation.id = obsmedia.observation_id

where s.visit_id=%(visit_id)s
and conf > %(deepfaune_threshold)s
and class = %(deepfaune_selection)s
and observation.observation_type_id = %(observation_type_id)s
and (observation.payload ->> '1')::numeric >= %(megadetector_threshold)s
and coalesce((observation.payload ->> '2')::numeric, 0) <= %(megadetector_threshold)s
and coalesce((observation.payload ->> '3')::numeric, 0) <= %(megadetector_threshold)s
order by  start_time, file.name
""",
                    {
                        "visit_id": visit_id,
                        "deepfaune_threshold": deepfaune_threshold,
                        "deepfaune_selection": deepfaune_selection,
                        "megadetector_threshold": megadetector_threshold,
                        "observation_type_id": observation_type.get_id("megadetector"),
                    },
                )

            # ----------------------------------
            elif (
                deepfaune_active
                and not megadetector_active
                and deepfaune_selection != "all"
            ):
                print("seulement deepfaune")
                cursor.execute(
                    """

select distinct on(start_time, file.name) 
    s.media_id,
    s.visit_id,
    s.field_sensor_id,
    file.name, 
    s.mime_type, 
    s.start_time, 
    s.duration, 
    file.path 
from camtrap.deepfaune_synthesis s
join camtrap.file on s.media_id = file.id
where s.visit_id=%(visit_id)s
and conf > %(deepfaune_threshold)s
and class = %(deepfaune_selection)s
order by  start_time, file.name
""",
                    {
                        "visit_id": visit_id,
                        "deepfaune_threshold": deepfaune_threshold,
                        "deepfaune_selection": deepfaune_selection,
                    },
                )
            # ----------------------------------
            elif (
                deepfaune_active
                and not megadetector_active
                and deepfaune_selection == "all"
            ):
                print("seulement deepfaune, toutes espèces")
                cursor.execute(
                    """

select distinct on(start_time, file.name) 
    s.media_id,
    s.visit_id,
    s.field_sensor_id,
    file.name, 
    s.mime_type, 
    s.start_time, 
    s.duration, 
    file.path 
from camtrap.deepfaune_synthesis s
join camtrap.file on s.media_id = file.id
where s.visit_id=%(visit_id)s
and conf > %(deepfaune_threshold)s
order by  start_time, file.name
""",
                    {
                        "visit_id": visit_id,
                        "deepfaune_threshold": deepfaune_threshold,
                        "deepfaune_selection": deepfaune_selection,
                    },
                )
            # ----------------------------------
            else:
                print("pas de filtre")
                cursor.execute(
                    """
select 
    media.id media_id,
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
            result = tuple(cursor)
            print(len(result))
            return result
