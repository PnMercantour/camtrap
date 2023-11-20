"""
media_component.py
select media/media group within the current project and filter contexts
"""
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update, ctx
from dash.exceptions import PreventUpdate
from datetime import datetime, timedelta
import json
import project_component
import filter_component

from functools import lru_cache
from pathlib import Path
from config import data_root


prev_button = dbc.Button(
    html.I(className="fas fa-solid fa-step-backward"),
    id="media:previous",
    title="Média précédent",
)

next_button = dbc.Button(
    html.I(className="fas fa-solid fa-step-forward"),
    id="media:next",
    title="Média suivant",
)

media_slider = dcc.Slider(
    id="media:index",
    min=1,
    max=100,
    step=1,
    included=False,
    marks=None,
    tooltip={"placement": "bottom", "always_visible": True},
)

first_in_group_button = dbc.Button(
    html.I(className="fas fa-solid fa-backward"),
    id="media:first_in_group",
    title="Premier média du groupe",
)

last_in_group_button = dbc.Button(
    html.I(className="fas fa-solid fa-forward"),
    id="media:last_in_group",
    title="Dernier média du groupe",
)

in_group_slider = dcc.Slider(
    id="media:in_group_index",
    min=1,
    max=100,
    step=1,
    included=False,
    marks=None,
    tooltip={"placement": "bottom", "always_visible": False},
)

prev_group_button = dbc.Button(
    html.I(className="fas fa-solid fa-fast-backward"),
    id="media:previous_group",
    title="Dernier média du groupe précédent",
)

next_group_button = dbc.Button(
    html.I(className="fas fa-solid fa-fast-forward"),
    id="media:next_group",
    title="Premier média du groupe suivant",
)

group_slider = dcc.Slider(
    id="media:group_index",
    min=1,
    max=100,
    step=1,
    included=False,
    marks=None,
    tooltip={"placement": "bottom", "always_visible": True},
)

group_interval = dbc.Select(
    id="media_group:interval",
    # clearable=False,
    value=600,
    options=[
        {"label": "5s", "value": 5},
        {"label": "10s", "value": 10},
        {"label": "30s", "value": 30},
        {"label": "1mn", "value": 60},
        {"label": "5mn", "value": 300},
        {"label": "10mn", "value": 600},
        {"label": "30mn", "value": 1800},
        {"label": "1h", "value": 3600},
        {"label": "3h", "value": 10800},
        {"label": "1 jour", "value": 86400},
        {"label": "1 mois", "value": 2592000},
    ],
)


def interval2str(interval):
    "convert a number to a display friendly string"
    if interval is None:
        return None
    if interval < 60:
        return f"{round(interval)} s"
    return str(timedelta(seconds=round(interval))) + " s"


component = dbc.Card(
    [
        dbc.CardHeader(["Médias"]),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col("Fichier", width=3),
                        dbc.Tooltip(id="media:path", target="media:fileName"),
                        dbc.Col(id="media:fileName"),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Tooltip("Date de prise de vue", target="media:startTime"),
                        dbc.Col("Date", width=3),
                        dbc.Col(id="media:startTime"),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Tooltip("Durée du média", target="media:duration"),
                        dbc.Col("Média", width=3),
                        dbc.Col(id="media:duration"),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col([prev_button, next_button], width=3),
                        dbc.Col(media_slider, width=9),
                    ]
                ),
                # html.Hr(),
                dbc.Row(
                    [
                        dbc.Col("Médias du groupe", width=3),
                        dbc.Tooltip(
                            "Durée du groupe de médias", target="media:group_duration"
                        ),
                        dbc.Col(id="media:group_duration"),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col([first_in_group_button, last_in_group_button], width=3),
                        dbc.Col(in_group_slider, width=9),
                    ]
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col("Groupes", width=3),
                        dbc.Col("Intervalle", width=3),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col([prev_group_button, next_group_button], width=3),
                        dbc.Col(group_interval, width=3),
                        dbc.Col(group_slider, width=6),
                    ]
                ),
                dcc.Store(id="camtrap:media_cookie", storage_type="local"),
            ]
        ),
    ]
)

interval = Input("media_group:interval", "value")
path = Input("media:path", "children")


# Each media can be retrieved from:
# - the project and filter context (which define the time/name ordered list of media to consider)
# - the index of the media in the above list
# Consecutive medias are grouped when end time /start time difference is smaller than interval
# (a number of seconds). metadata MUST be sorted by time ascending and name ascending.
# Once computed, a media group can be encoded as the start / end indexes of medias in the group
@lru_cache
def groups_table(visit_id, filter_context, interval):
    """returns the groups table"""
    # start_datetime and end_datetime properties are datetime objects
    delta = timedelta(seconds=int(interval))
    metadata = filter_component.metadata(visit_id, filter_context)
    g = None
    groups = []
    end_datetime = None
    for idx, md in enumerate(metadata):
        start_datetime = md["start_time"]
        if end_datetime is None or end_datetime + delta < start_datetime:
            g = dict(start=idx, end=idx, start_datetime=start_datetime)
            groups.append(g)
        end_datetime = start_datetime + timedelta(seconds=float(md["duration"]))
        g["end_datetime"] = end_datetime
        g["end"] = idx
    return groups


def group_info(groups, media_idx):
    "returns the group idx for <media_idx>"
    for idx, group in enumerate(groups):
        if group["start"] <= media_idx and group["end"] >= media_idx:
            return idx


@dash.callback(
    output={
        "group_control": dict(
            index=Output(group_slider, "value"),
            max=Output(group_slider, "max"),
            marks=Output(group_slider, "marks"),
            disable_prev=Output(prev_group_button, "disabled"),
            disable_next=Output(next_group_button, "disabled"),
        ),
        "group_local_control": dict(
            index=Output(in_group_slider, "value"),
            max=Output(in_group_slider, "max"),
            marks=Output(in_group_slider, "marks"),
            disable_first=Output(first_in_group_button, "disabled"),
            disable_last=Output(last_in_group_button, "disabled"),
        ),
        "media_control": dict(
            index=Output(media_slider, "value"),
            max=Output(media_slider, "max"),
            marks=Output(media_slider, "marks"),
            disable_prev=Output(prev_button, "disabled"),
            disable_next=Output(next_button, "disabled"),
        ),
        "media_info": dict(
            cookie=Output("camtrap:media_cookie", "data"),
            path=Output("media:path", "children"),
            file_name=Output("media:fileName", "children"),
            start_time=Output("media:startTime", "children"),
            duration=Output("media:duration", "children"),
            group_duration=Output("media:group_duration", "children"),
        ),
    },
    inputs={
        "project_context": project_component.input,
        "filter_context": filter_component.input,
        "interval_ctl": Input(group_interval, "value"),
        "grp_ctl_in": {
            "current": Input(group_slider, "value"),
            "previous": Input(prev_group_button, "n_clicks"),
            "next": Input(next_group_button, "n_clicks"),
        },
        "grp_local_ctl_in": {
            "current": Input(in_group_slider, "value"),
            "first": Input(first_in_group_button, "n_clicks"),
            "last": Input(last_in_group_button, "n_clicks"),
        },
        "media_ctl_in": {
            "current": Input(media_slider, "value"),
            "previous": Input(prev_button, "n_clicks"),
            "next": Input(next_button, "n_clicks"),
        },
    },
)
def update(
    project_context,
    filter_context,
    interval_ctl,
    grp_ctl_in,
    grp_local_ctl_in,
    media_ctl_in,
):
    visit_id = project_context["visit_id"]
    metadata = filter_component.metadata(visit_id, filter_context)
    metadata_size = len(metadata)

    if metadata_size == 0:
        grp_ctl_out = dict(
            index=None,
            max=1,
            marks={1: "vide"},
            disable_prev=False,
            disable_next=False,
        )
        grp_local_ctl_out = dict(
            index=None,
            max=1,
            marks={1: "vide"},
            disable_first=True,
            disable_last=True,
        )
        media_ctl_out = dict(
            index=None,
            max=1,
            marks={1: "vide"},
            disable_prev=False,
            disable_next=False,
        )
        info = dict(
            cookie=None,
            path=None,
            file_name=None,
            start_time=None,
            duration=None,
            group_duration=None,
        )
    else:
        groups = groups_table(visit_id, filter_context, interval_ctl)
        groups_size = len(groups)

        if ctx.triggered_id in [
            None,
            project_component.visit.id,
            filter_component.megadetector.id,
            group_interval.id,
        ]:
            g_idx = 0
            current_group = groups[g_idx]
            current_group_size = current_group["end"] - current_group["start"] + 1
            media_idx = 0

        elif ctx.triggered_id in [
            group_slider.id,
            prev_group_button.id,
            next_group_button.id,
        ]:
            input_g_idx = grp_ctl_in["current"] - 1
            if ctx.triggered_id == group_slider.id:
                g_idx = input_g_idx
            elif ctx.triggered_id == prev_group_button.id:
                g_idx = max(input_g_idx - 1, 0)
            else:
                g_idx = min(input_g_idx + 1, groups_size - 1)

            current_group = groups[g_idx]
            if ctx.triggered_id == group_slider.id:
                media_idx = current_group["start"]
            elif ctx.triggered_id == prev_group_button.id:
                media_idx = current_group["end"]
            else:
                media_idx = current_group["start"]

        elif ctx.triggered_id in [
            media_slider.id,
            prev_button.id,
            next_button.id,
        ]:
            input_media_idx = media_ctl_in["current"] - 1
            initial_g_idx = grp_ctl_in["current"] - 1
            initial_group = groups[initial_g_idx]
            if ctx.triggered_id == next_button.id:
                media_idx = min(input_media_idx + 1, metadata_size - 1)
                if media_idx > initial_group["end"]:
                    g_idx = initial_g_idx + 1
                else:
                    g_idx = initial_g_idx
            elif ctx.triggered_id == prev_button.id:
                media_idx = max(input_media_idx - 1, 0)
                if media_idx < initial_group["start"]:
                    g_idx = initial_g_idx - 1
                else:
                    g_idx = initial_g_idx
            else:
                media_idx = input_media_idx
                g_idx = group_info(groups, media_idx)

        elif ctx.triggered_id in [
            in_group_slider.id,
            first_in_group_button.id,
            last_in_group_button.id,
        ]:
            g_idx = grp_ctl_in["current"] - 1
            current_group = groups[g_idx]
            if ctx.triggered_id == last_in_group_button.id:
                media_idx = current_group["end"]
            elif ctx.triggered_id == first_in_group_button.id:
                media_idx = current_group["start"]
            else:
                input_g_local_idx = grp_local_ctl_in["current"] - 1
                media_idx = current_group["start"] + input_g_local_idx

        else:
            print("media: unhandled event")
            raise PreventUpdate
        current_group = groups[g_idx]
        current_group_size = current_group["end"] - current_group["start"] + 1
        g_local_idx = media_idx - current_group["start"]

        grp_ctl_out = dict(
            index=g_idx + 1,
            max=groups_size,
            marks={groups_size: str(groups_size)},
            disable_prev=(g_idx == 0),
            disable_next=(g_idx == groups_size - 1),
        )
        grp_local_ctl_out = dict(
            index=g_local_idx + 1,
            max=current_group_size,
            marks={current_group_size: str(current_group_size)},
            disable_first=(g_local_idx == 0),
            disable_last=(g_local_idx == current_group_size - 1),
        )
        media_ctl_out = dict(
            index=media_idx + 1,
            max=metadata_size,
            marks={metadata_size: str(metadata_size)},
            disable_prev=(media_idx == 0),
            disable_next=(media_idx == metadata_size - 1),
        )
        info = dict(
            cookie=dict(
                metadata[media_idx],
                filter_context=filter_context,
                group_start_idx=current_group["start"],
                group_end_idx=current_group["end"],
                current_group_size=current_group_size,
                media_idx=media_idx,
                interval_ctl=interval_ctl,
            ),
            path=metadata[media_idx]["path"],
            file_name=metadata[media_idx]["name"],
            start_time=str(metadata[media_idx]["start_time"]),
            duration=interval2str(metadata[media_idx]["duration"]),
            group_duration=str(
                metadata[current_group["end"]]["start_time"]
                + timedelta(seconds=round(metadata[current_group["end"]]["duration"]))
                - metadata[current_group["start"]]["start_time"]
            ),
        )
    return {
        "group_control": grp_ctl_out,
        "group_local_control": grp_local_ctl_out,
        "media_control": media_ctl_out,
        "media_info": info,
    }
