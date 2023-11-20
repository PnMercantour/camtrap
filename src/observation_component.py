import dash_bootstrap_components as dbc
import dash
from dash import callback, Output, Input, State, html, ctx, ALL, no_update
import psycopg
import json
from psycopg.rows import dict_row
from datetime import timedelta, datetime
from config import (
    POSTGRES_CONNECTION,
    OBSERVATION_WINDOW,
    wildlife_options,
    domestic_options,
    other_options,
)
from auth import trusted_user
import filter_component

PROJECT = 1
OBSERVATION_VERSION = 1

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

category_options = {
    "wildlife": wildlife_options,
    "domestic": domestic_options,
    "other": other_options,
}

name = dbc.Select(
    placeholder="Sélectionner une valeur ...",
    options=wildlife_options,
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
    category=Input(category, "value"),
    name=State(name, "value"),
    population=State(population, "value"),
    comment=State(comment, "value"),
)

payload_output = dict(
    category=Output(category, "value"),
    options=Output(name, "options"),
    name=Output(name, "value"),
    population=Output(population, "value"),
    comment=Output(comment, "value"),
)


def reset_payload(category):
    return dict(
        category=category,
        options=category_options[category],
        name=None,
        population=None,
        comment=None,
    )


fresh_payload = reset_payload("wildlife")


def init_payload(id, observations):
    payload = next(o["payload"] for o in observations if o["id"] == id)
    category = payload.get("category")
    return {
        "category": category,
        "options": category_options[category],
        "name": payload.get("name"),
        "population": payload.get("population")
        if category in ("wildlife", "domestic")
        else None,
        "comment": payload.get("comment"),
    }


observation_fields = [
    observation_id,
    show_group,
    category,
    name,
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
            ]
        ),
    ]
)


# -----------------------------
# Display existing observations
# -----------------------------
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
                return f'Faune sauvage: {payload.get("name")}{population}'
            else:
                return f'Faune domestique: {payload.get("name")}{population}'

        else:
            return f'Autre observation: {payload.get("name")}'

    return html.Div([view_main(), html.Br(), payload.get("comment")])


megadetector_category_dict = {
    "1": "Animal",
    "2": "Humain",
    "3": "Véhicule",
}


def view_megadetector_payload(payload):
    return html.Div(
        [
            f"{megadetector_category_dict[key]}: {value} "
            for key, value in payload.items()
        ]
    )


def view_observation(row, media_context):
    active = media_context["id"] in row["medias"]
    # TODO: fix this hack
    if row["observation_type_id"] == 2:
        if active:
            return dbc.ListGroupItem(
                [
                    f"{row['digitizer']}",
                    html.Br(),
                    view_megadetector_payload(row["payload"]),
                    # str(row["payload"]),
                ],
                active=active,
            )
        else:
            return
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
                "Editer",
                id={
                    "type": "observation",
                    "action": "edit",
                    "id": row["id"],
                },
                title="Editer l'observation",
            )
            if active
            else None,
            dbc.Button(
                "Supprimer",
                id={
                    "type": "observation",
                    "action": "delete",
                    "id": row["id"],
                },
                title="Supprimer l'observation",
            )
            if active
            else None,
            dbc.Button(
                "Etendre",
                id={
                    "type": "observation",
                    "action": "add_media",
                    "id": row["id"],
                },
                title="Ajouter ce media à l'observation",
            )
            if not active
            else dbc.Button(
                "Réduire",
                id={
                    "type": "observation",
                    "action": "remove_media",
                    "id": row["id"],
                },
                title="Retirer ce media de l'observation",
            )
            if len(row["medias"]) > 1
            else None,
            # dbc.Button(
            #     "Réduire",
            #     id={
            #         "type": "observation",
            #         "action": "remove_media",
            #         "id": row["id"],
            #     },
            #     title="Retirer ce media de l'observation",
            # )
            # if active
            # else dbc.Button(
            #     "Etendre",
            #     id={
            #         "type": "observation",
            #         "action": "add_media",
            #         "id": row["id"],
            #     },
            #     title="Ajouter ce media à l'observation",
            # ),
        ],
        active=active,
    )


def list_medias(media_context, group_mode):
    "returns media_id depending on group_mode switch: either all media_id of current group if group_mode or just a singleton"
    if group_mode:
        visit_id = media_context["visit_id"]
        filter_context = media_context["filter_context"]
        group_start_idx = media_context["group_start_idx"]
        group_end_idx = media_context["group_end_idx"]
        metadata = filter_component.metadata(visit_id, filter_context)
        return [md["id"] for md in metadata[group_start_idx : group_end_idx + 1]]
    else:
        return [media_context["id"]]


def payload_to_db(payload):
    return json.dumps(
        dict(
            payload,
            version=OBSERVATION_VERSION,
        )
    )


def insert_observation(payload, media_id_list):
    "creates an observation in database, attached to all media in media_id_list"
    print("new observation:", media_id_list)
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
                    "version": OBSERVATION_VERSION,
                    "project_id": PROJECT,
                    "digitizer": trusted_user(),
                    "payload": payload_to_db(payload),
                },
            )
            observation_id = cursor.fetchone()["id"]
            print("new observation", observation_id)
            for media_id in media_id_list:
                cursor.execute(
                    """
insert into camtrap.obsmedia(observation_id, media_id, ref)
values(%(observation_id)s, %(media_id)s, %(ref)s)
""",
                    {
                        "observation_id": observation_id,
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
                    "payload": payload_to_db(payload),
                },
            )


def select_observations(media_context):
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
with selection as (
select
	observation.id
from
	camtrap.observation
join camtrap.obsmedia on
	observation.id = obsmedia.observation_id
join camtrap.media on
	obsmedia.media_id = media.id
where
	media.visit_id = %(visit_id)s
	and media.start_time between %(window_start)s and %(window_end)s
            )
select
	observation.id,
	observation.digitizer,
	observation.digit_timestamp,
	observation.observation_type_id,
	observation.payload,
	min(media.start_time) start_time,
	max(media.start_time + (media.duration || 's')::interval) end_time,
	array_agg(distinct media_id) medias
from
	camtrap.observation
join selection
		using(id)
join camtrap.obsmedia on
	observation.id = obsmedia.observation_id
join camtrap.media on
	obsmedia.media_id = media.id
group by
	observation.id
order by
	start_time
""",
                {
                    "visit_id": media_context["visit_id"],
                    "window_start": datetime.fromisoformat(media_context["start_time"])
                    - timedelta(minutes=OBSERVATION_WINDOW),
                    "window_end": datetime.fromisoformat(media_context["start_time"])
                    + timedelta(minutes=OBSERVATION_WINDOW),
                },
            )
            return [row for row in cursor]


def delete_observation(id):
    print("delete observation", id)
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
delete from camtrap.observation 
where id = %(id)s 
""",
                {"id": id},
            )


def add_media(media_id, observation_id):
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
insert into camtrap.obsmedia (observation_id, media_id, ref)
values(%(observation_id)s, %(media_id)s, %(ref)s)
""",
                {
                    "observation_id": observation_id,
                    "media_id": media_id,
                    "ref": None,
                },
            )


def remove_media(media_id, observation_id):
    with psycopg.connect(POSTGRES_CONNECTION, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
delete from camtrap.obsmedia 
where observation_id = %(observation_id)s and  media_id = %(media_id)s
""",
                {
                    "observation_id": observation_id,
                    "media_id": media_id,
                },
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
        "media_context": Input("camtrap:media_cookie", "data"),
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
    media_context,
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
    if media_context is None:
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
    if edition_mode:
        if ctx.triggered_id == category.id:
            return {
                "edition_mode": no_update,
                "insert_mode": no_update,
                "id": no_update,
                "payload": reset_payload(payload["category"]),
                "observations": None,
            }
        if ctx.triggered_id == commit_btn.id:
            if insert_mode:
                insert_observation(payload, list_medias(media_context, group_mode))
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
                ctx.triggered_id.id,
                select_observations(media_context),
            ),
            "observations": None,
        }
    elif ctx.triggered_id.action == "delete":
        delete_observation(ctx.triggered_id.id)
    elif ctx.triggered_id.action == "add_media":
        add_media(media_context["id"], ctx.triggered_id.id)
    elif ctx.triggered_id.action == "remove_media":
        remove_media(media_context["id"], ctx.triggered_id.id)
    obs = select_observations(media_context)
    return {
        "edition_mode": False,
        "insert_mode": no_update,
        "id": no_update,
        "payload": fresh_payload,
        "observations": [
            view_observation(observation, media_context) for observation in obs
        ],
    }
