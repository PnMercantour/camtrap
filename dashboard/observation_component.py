import dash_bootstrap_components as dbc
import dash
from dash import callback, Output, Input, State, html, ctx, ALL, no_update
import psycopg
import json
from psycopg.rows import dict_row
from datetime import timedelta, datetime
from config import (
    POSTGRES_CONNECTION,
    wildlife_options,
    domestic_options,
    other_options,
)
from auth import trusted_user
import project_component
import media_component

PROJECT = 1
VERSION = 1
WINDOW = 30

group_mode_switch = dbc.Switch(label="Appliquer au groupe", value=False)
show_group = dbc.Collapse(group_mode_switch, is_open=True)

category = dbc.RadioItems(
    options=[
        {"label": "Faune sauvage", "value": "wildlife"},
        {"label": "Faune domestique", "value": "domestic"},
        {"label": "Autre contenu", "value": "other"},
    ],
    value="wildlife",
)

wildlife = dbc.Select(
    placeholder="Faune sauvage",
    options=wildlife_options,
)

domestic = dbc.Select(
    placeholder="Faune domestique",
    options=domestic_options,
)

other = dbc.Select(
    placeholder="Autre",
    options=other_options,
)

population = dbc.Input(
    placeholder="Nombre d'individus",
    type="number",
)

comment = dbc.Input(
    placeholder="Commentaire...",
    type="text",
)

observation_id = dbc.Input(
    type="number",
    disabled=True,
)

cancel_btn = dbc.Button("Abandonner")
commit_btn = dbc.Button("Enregistrer")


payload_input = dict(
    category=State(category, "value"),
    wildlife=State(wildlife, "value"),
    domestic=State(domestic, "value"),
    other=State(other, "value"),
    population=State(population, "value"),
    comment=State(comment, "value"),
)

payload_output = dict(
    category=Output(category, "value"),
    wildlife=Output(wildlife, "value"),
    domestic=Output(domestic, "value"),
    other=Output(other, "value"),
    population=Output(population, "value"),
    comment=Output(comment, "value"),
)

fresh_payload = dict(
    category="wildlife",
    wildlife=None,
    domestic=None,
    other=None,
    population=None,
    comment=None,
)


def init_payload(id, observations):
    payload = next(o["payload"] for o in observations if o["id"] == id)
    category = payload.get("category")
    return {
        "category": category,
        "wildlife": payload.get("wildlife") if category == "wildlife" else None,
        "domestic": payload.get("domestic") if category == "domestic" else None,
        "other": payload.get("other") if category == "other" else None,
        "population": payload.get("population")
        if category in ("wildlife", "domestic")
        else None,
        "comment": payload.get("comment"),
    }


observation_fields = [
    observation_id,
    show_group,
    category,
    wildlife,
    domestic,
    other,
    population,
    comment,
    cancel_btn,
    commit_btn,
]


component = dbc.Card(
    [
        dbc.CardHeader(
            dbc.Row(
                [
                    dbc.Col("Observations", width="auto"),
                    dbc.Col(add_observation_btn := dbc.Button("+")),
                ],
                align="center",
                justify="between",
            )
        ),
        dbc.CardBody(
            [
                show_editor := dbc.Collapse(
                    edit := html.Div(observation_fields),
                    is_open=False,
                ),
                observations := dbc.ListGroup(),
                html.Div(id="debug_observation"),
            ]
        ),
    ]
)


def view_payload(payload):
    def view_main():
        category = payload.get("category")
        if category in ("wildlife", "domestic"):
            population = (
                f' ({payload["population"]} individus)'
                if payload["population"] is not None
                else ""
            )
            if category == "wildlife":
                return f'Faune sauvage: {payload.get("wildlife")}{population}'
            else:
                return f'Faune domestique: {payload.get("domestic")}{population}'

        else:
            return f'Autre observation: {payload.get("other")}'

    return html.Div([view_main(), html.Br(), payload.get("comment")])


def view_observation(row, media_metadata):
    return dbc.ListGroupItem(
        [
            view_payload(row["payload"]),
            html.Br(),
            f"De {row['start_time']} à {row['end_time']}, {len(row['medias'])} media(s)",
            html.Br(),
            f"par {row['digitizer']}",
            html.Br(),
            html.Br(),
            dbc.Button(
                "Modifier",
                id={
                    "type": "observation",
                    "action": "edit",
                    "id": row["id"],
                },
                title="Modifier l'observation",
            ),
            dbc.Button(
                "Supprimer",
                id={
                    "type": "observation",
                    "action": "delete",
                    "id": row["id"],
                },
                title="Supprimer l'observation",
            ),
        ],
        active=media_metadata["id"] in row["medias"],
    )


def list_medias(media_metadata, group_mode):
    "returns a list of media_id"
    if group_mode:
        visit_id = media_metadata["visit_id"]
        group_start_idx = media_metadata["group_start_idx"]
        group_end_idx = media_metadata["group_end_idx"]
        metadata = project_component.metadata(visit_id)
        return [md["id"] for md in metadata[group_start_idx : group_end_idx + 1]]
    else:
        return [media_metadata["id"]]


def insert_observation(payload, media_metadata, group_mode):
    print("insert")
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
with observation_type as (select id from camtrap.observation_type where application = %(application)s and version = %(version)s)
insert into camtrap.observation(project_id, digitizer, observation_type_id, payload) 
select %(project_id)s, %(digitizer)s, observation_type.id, %(payload)s from observation_type
returning id
""",
                {
                    "application": "observation",
                    "version": VERSION,
                    "project_id": PROJECT,
                    "digitizer": trusted_user(),
                    "payload": json.dumps(
                        dict(
                            payload,
                            version=VERSION,
                        )
                    ),
                },
            )
            id = cursor.fetchone()["id"]
            for media_id in list_medias(media_metadata, group_mode):
                cursor.execute(
                    """
insert into camtrap.obsmedia(observation_id, media_id, ref)
values(%(id)s, %(media_id)s, %(ref)s)
returning id
""",
                    {
                        "id": id,
                        "media_id": media_id,
                        "ref": None,
                    },
                )


def update_observation(id, payload):
    print("update")
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
update camtrap.observation
set 
digitizer = %(digitizer)s, 
payload = %(payload)s 
where id = %(id)s
                """,
                {
                    "id": id,
                    "digitizer": trusted_user(),
                    "payload": json.dumps(
                        dict(
                            payload,
                            version=VERSION,
                        )
                    ),
                },
            )


def select_observations(media_metadata):
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
with selection as (select observation.id from camtrap.observation 
join camtrap.obsmedia on observation.id = obsmedia.observation_id
join camtrap.media on obsmedia.media_id = media.id
where media.visit_id = %(visit_id)s
and media.start_time between %(window_start)s and %(window_end)s
            )
select 
observation.id, 
observation.digitizer,
observation.digit_timestamp,
observation.observation_type_id,
observation.payload,
min(media.start_time) start_time, 
max(media.start_time + (media.duration||'s')::interval) end_time, 
array_agg(distinct media_id) medias
from camtrap.observation
join selection using(id)
join camtrap.obsmedia on observation.id = obsmedia.observation_id
join camtrap.media on obsmedia.media_id = media.id
group by observation.id 
order by start_time
""",
                {
                    "visit_id": media_metadata["visit_id"],
                    "window_start": datetime.fromisoformat(media_metadata["start_time"])
                    - timedelta(minutes=WINDOW),
                    "window_end": datetime.fromisoformat(media_metadata["start_time"])
                    + timedelta(minutes=WINDOW),
                },
            )
            return [row for row in cursor]


def delete_observation(id):
    print("delete")
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
delete from camtrap.observation 
where id = %(id)s 
""",
                {"id": id},
            )


@callback(
    output={
        "edition_mode": Output(show_editor, "is_open"),
        "insert_mode": Output(show_group, "is_open"),
        "id": Output(observation_id, "value"),
        "payload": payload_output,
        "observations": Output(observations, "children"),
    },
    inputs={
        "media_metadata": Input("camtrap:media_id", "data"),
        "add_observation": Input(add_observation_btn, "n_clicks"),
        "edition_mode": State(show_editor, "is_open"),
        "insert_mode": State(show_group, "is_open"),
        "group_mode": State(group_mode_switch, "value"),
        "commit": Input(commit_btn, "n_clicks"),
        "cancel": Input(cancel_btn, "n_clicks"),
        "id": State(observation_id, "value"),
        "payload": payload_input,
        "list_actions": Input(
            {"type": "observation", "action": ALL, "id": ALL}, "n_clicks"
        ),
    },
)
def update(
    media_metadata,
    add_observation,
    edition_mode,
    insert_mode,
    group_mode,
    commit,
    cancel,
    id,
    payload,
    list_actions,
):
    if media_metadata is None:
        return {
            "edition_mode": False,
            "insert_mode": no_update,
            "id": None,
            "payload": fresh_payload,
            "observations": None,
        }
    if ctx.triggered_id == add_observation_btn.id:
        return {
            "edition_mode": True,
            "insert_mode": True,
            "id": None,
            "payload": fresh_payload,
            "observations": None,
        }
    print(ctx.triggered_id)
    print(list_actions)
    if edition_mode:
        if ctx.triggered_id == commit_btn.id:
            if insert_mode:
                insert_observation(payload, media_metadata, group_mode)
            else:
                update_observation(id, payload)
    elif not any([click is not None for click in list_actions]):
        # prevent_initial_call=True does not inhibit initialization events from dynamically created components.
        pass
    elif ctx.triggered_id.action == "edit":
        return {
            "edition_mode": True,
            "insert_mode": False,
            "id": ctx.triggered_id.id,
            "payload": init_payload(
                ctx.triggered_id.id, select_observations(media_metadata)
            ),
            "observations": None,
        }
    elif ctx.triggered_id.action == "delete":
        delete_observation(ctx.triggered_id.id)
    obs = select_observations(media_metadata)
    return {
        "edition_mode": False,
        "insert_mode": no_update,
        "id": no_update,
        "payload": fresh_payload,
        "observations": [
            view_observation(observation, media_metadata) for observation in obs
        ],
    }
