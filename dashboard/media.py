import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
from datetime import datetime, timedelta
import json
from metadata import listSites, getVisitMetadata
import selection
import filter
from functools import lru_cache
from pathlib import Path
from config import data_root


prev_button = dbc.Button(html.I(className="fas fa-solid fa-step-backward"),
                         id='media:previous', title='Média précédent')

next_button = dbc.Button(html.I(className="fas fa-solid fa-step-forward"),
                         id='media:next', title='Média suivant')

item_slider = dcc.Slider(id="media:index", min=1, max=100, step=1, included=False, marks=None, tooltip={
    'placement': 'bottom', 'always_visible': True},)

first_in_group_button = dbc.Button(html.I(className="fas fa-solid fa-backward"),
                                   id='media:first_in_group', title='Premier média du groupe')

last_in_group_button = dbc.Button(html.I(className="fas fa-solid fa-forward"),
                                  id='media:last_in_group', title='Dernier média du groupe')

in_group_slider = dcc.Slider(id="media:in_group_index", min=1, max=100, step=1, included=False, marks=None, tooltip={
    'placement': 'bottom', 'always_visible': True},)

prev_group_button = dbc.Button(html.I(className="fas fa-solid fa-fast-backward"),
                               id='media:previous_group', title='Dernier média du groupe précédent')

next_group_button = dbc.Button(html.I(className="fas fa-solid fa-fast-forward"),
                               id='media:next_group', title='Premier média du groupe suivant')

group_slider = dcc.Slider(id="media:group_index", min=1, max=100, step=1, included=False, marks=None, tooltip={
    'placement': 'bottom', 'always_visible': True},)

group_interval = dcc.Dropdown(
    id='media_group:interval',
    clearable=False,
    value=600,
    options=[
        {'label': '5s', 'value': 5},
        {'label': '10s', 'value': 10},
        {'label': '30s', 'value': 30},
        {'label': '1mn', 'value': 60},
        {'label': '5mn', 'value': 300},
        {'label': '10mn', 'value': 600},
        {'label': '30mn', 'value': 1800},
        {'label': '1h', 'value': 3600},
        {'label': '3h', 'value': 10800},
        {'label': '1 jour', 'value': 86400},
        {'label': '1 mois', 'value': 2592000},
    ],
)


def interval2str(interval):
    "convert a number to a display friendly string"
    if interval is None:
        return None
    if interval < 60:
        return f"{round(interval)} s"
    return str(timedelta(seconds=round(interval))) + ' s'


card = dbc.Card([
    dbc.CardHeader([
        "Médias",
    ]),
    dbc.CardBody([
        dbc.Row([
            dbc.Col("Fichier", width=3),
            dbc.Tooltip(id='media:path', target='media:fileName'),
            dbc.Col(id='media:fileName'),
        ]),
        dbc.Row([
            dbc.Col("Date", width=3),
            dbc.Col(id='media:startTime'),
        ]),
        dbc.Row([
            dbc.Tooltip("Durée du média", target='media:duration'),
            dbc.Col('Média', width=3),
            dbc.Col(id='media:duration'),
        ]),
        dbc.Row([
            dbc.Col([prev_button, next_button], width=3),
            dbc.Col(item_slider, width=9),
        ]),
        dbc.Row([
            dbc.Col("Groupe", width=3),
            dbc.Tooltip("Durée du groupe de médias",
                        target='media:group_duration'),
            dbc.Col(id='media:group_duration'),
        ]),
        dbc.Row([
            dbc.Col([first_in_group_button, last_in_group_button], width=3),
            dbc.Col(in_group_slider, width=9),
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col('Groupes', width=3),
            dbc.Col('Intervalle', width=3),
        ]),
        dbc.Row([
            dbc.Col([prev_group_button, next_group_button], width=3),
            dbc.Col(group_interval, width=3),
            dbc.Col(group_slider, width=6),
        ]),
        dcc.Store(id='media:cookie', storage_type='local'),
    ])
])

output = dict(
    media=dict(
        index=Output(item_slider, 'value'),
        max=Output(item_slider, 'max'),
        marks=Output(item_slider, 'marks'),
    ),
    in_group=dict(
        index=Output('media:in_group_index', 'value'),
        max=Output('media:in_group_index', 'max'),
        marks=Output('media:in_group_index', 'marks'),
    ),
    group=dict(
        index=Output('media:group_index', 'value'),
        max=Output('media:group_index', 'max'),
        marks=Output('media:group_index', 'marks'),
    ),
    control=dict(
        disable_previous=Output('media:previous', "disabled"),
        disable_next=Output('media:next', 'disabled'),
        disable_first_in_group=Output('media:first_in_group', 'disabled'),
        disable_last_in_group=Output('media:last_in_group', 'disabled'),
        disable_previous_group=Output('media:previous_group', 'disabled'),
        disable_next_group=Output('media:next_group', 'disabled'),
    ),
    info=dict(
        path=Output('media:path', 'children'),
        file_name=Output('media:fileName', 'children'),
        start_time=Output('media:startTime', 'children'),
        duration=Output('media:duration', 'children'),
        group_duration=Output('media:group_duration', 'children'),
    ),
    cookie=Output('media:cookie', 'data'),
)


local_context = dict(
    media_index=Input(item_slider, "value"),
    in_group_index=Input('media:in_group_index', 'value'),
    group_index=Input('media:group_index', 'value'),
    control=dict(
        previous=Input('media:previous', 'n_clicks'),
        next=Input('media:next', 'n_clicks'),
        first_in_group=Input('media:first_in_group', 'n_clicks'),
        last_in_group=Input('media:last_in_group', 'n_clicks'),
        previous_group=Input('media:previous_group', 'n_clicks'),
        next_group=Input('media:next_group', 'n_clicks'),
    ),
    cookie=State("media:cookie", "data"))

interval = Input('media_group:interval', 'value')
path = Input('media:path', 'children')


def compute_output(context, md_dict):
    metadata = md_dict['metadata']
    groups = md_dict['groups']
    if metadata is None or len(metadata) == 0:
        return dict(
            media=dict(
                index=None,
                max=no_update,
                marks=None,
            ),
            in_group=dict(
                index=None,
                max=None,
                marks=None
            ),
            group=dict(
                index=None,
                max=None,
                marks=None
            ),
            control=dict(
                disable_previous=True,
                disable_next=True,
                disable_first_in_group=True,
                disable_last_in_group=True,
                disable_previous_group=True,
                disable_next_group=True,
            ),
            info=dict(
                path=None,
                file_name=None,
                start_time=None,
                duration=None,
                group_duration=None,
            ),
            cookie=None,
        )

    def attr(media_index):
        "-1 stands for last available index"
        md_idx = media_index - 1 if media_index > 0 else len(metadata) - 1
        for idx, group in enumerate(groups):
            if group["start"] <= md_idx and group["end"] >= md_idx:
                return ({
                    "media_index": md_idx + 1,
                    "in_group_index": md_idx - group["start"] + 1,
                    "group_index": idx + 1,
                    "in_group_max": group["end"] - group["start"] + 1,
                    "group_max": len(groups),
                    "group_duration": (group['end_datetime'] - group['start_datetime']).total_seconds(),
                })
        raise ValueError((groups, media_index))

    def group_info(group_index):
        group = groups[group_index - 1]
        return {"first_media_index": group["start"] + 1, "last_media_index": group["end"] + 1}

    triggers = [trigger['prop_id'] for trigger in callback_context.triggered]
    media_triggers = [trigger for trigger in triggers if 'media:' in trigger]
    if len(media_triggers) > 0:
        print(media_triggers)
        trigger = media_triggers[0]
        # we don't expect multiple triggers. Process the first one
        if trigger == 'media:index.value':
            media_index = context['media_index']
        elif trigger == 'media:in_group_index.value':
            media_index = group_info(context['group_index'])[
                'first_media_index'] + context['in_group_index'] - 1
        elif trigger == 'media:group_index.value':
            media_index = group_info(context['group_index'])[
                'first_media_index']
        elif trigger == 'media:previous.n_clicks':
            media_index = context['media_index'] - 1
        elif trigger == 'media:next.n_clicks':
            media_index = context['media_index'] + 1
        elif trigger == 'media:first_in_group.n_clicks':
            media_index = group_info(context['group_index'])[
                'first_media_index']
        elif trigger == 'media:last_in_group.n_clicks':
            media_index = group_info(context['group_index'])[
                'last_media_index']
        elif trigger == 'media:previous_group.n_clicks':
            media_index = group_info(
                context["group_index"] - 1)['last_media_index']
        elif trigger == 'media:next_group.n_clicks':
            media_index = group_info(
                context["group_index"] + 1)['first_media_index']
        else:
            print('Unhandled trigger', trigger)
            # reset to stable values
            media_index = 1
    else:
        # not a media trigger, find the closest item if still on the same visit
        media_index = 1  # fallback value
        old_cookie = context['cookie']
        if old_cookie is not None and md_dict['visit'] == old_cookie.get("visit") and md_dict['site_id'] == old_cookie.get('site_id'):
            for idx, md in enumerate(metadata):
                media_index = idx + 1
                if md['fileName'] == old_cookie['fileName']:
                    break
                if md['startTime'] > old_cookie['startTime']:
                    break
            else:
                media_index = 1
    md = metadata[media_index - 1]
    cookie = dict(md, visit=md_dict["visit"], site_id=md_dict["site_id"])
    outp = attr(media_index)
    media_max = len(metadata)
    media_marks = {}
    media_marks[media_max] = str(media_max)
    in_group_max = outp['in_group_max']
    in_group_marks = {}
    in_group_marks[in_group_max] = str(in_group_max)
    group_max = len(groups)
    group_marks = {}
    group_marks[group_max] = str(group_max)
    return dict(
        media=dict(
            index=outp['media_index'],
            max=media_max,
            marks=media_marks,
        ),
        in_group=dict(
            index=outp['in_group_index'],
            max=in_group_max,
            marks=in_group_marks,
        ),
        group=dict(
            index=outp['group_index'],
            max=group_max,
            marks=group_marks,
        ),
        control=dict(
            disable_previous=outp['media_index'] == 1,
            disable_next=outp['media_index'] == media_max,
            disable_first_in_group=outp['in_group_index'] == 1,
            disable_last_in_group=outp['in_group_index'] == in_group_max,
            disable_previous_group=outp['group_index'] == 1,
            disable_next_group=outp['group_index'] == group_max,
        ),
        info=dict(
            path=md['path'],
            file_name=md['fileName'],
            start_time=datetime.fromisoformat(
                md['startTime']).isoformat(sep=' ', timespec='seconds'),
            duration=interval2str(md['duration']),
            group_duration=interval2str(outp['group_duration']),
        ),
        cookie=cookie,
    )


def groupMedias(metadata, interval):
    """  Group medias when end time /start time difference is smaller than interval (a number of seconds). metadata MUST be sorted by time ascending"""
    # start_datetime and end_datetime properties are datetime objects
    delta = timedelta(seconds=interval)
    g = None
    groups = []
    end_datetime = None
    for idx, md in enumerate(metadata):
        start_datetime = datetime.fromisoformat(md['startTime'])
        if end_datetime is None or end_datetime + delta < start_datetime:
            g = dict(start=idx, end=idx, start_datetime=start_datetime)
            groups.append(g)
        end_datetime = start_datetime + timedelta(seconds=md['duration'])
        g['end_datetime'] = end_datetime
        g['end'] = idx
    return groups


@ lru_cache(maxsize=64)
def build_groups(interval, visit, site_id, filter_s):
    # result from filterMetadata is shared among all values of group_context
    md_dict = filter.filterMetadata(visit, site_id, filter_s)
    groups = groupMedias(md_dict['metadata'], interval)
    return dict(md_dict, groups=groups)


@ dash.callback(
    output=[
        output,
    ],
    inputs=[
        local_context,
        interval,
        filter.context,
        selection.context,
    ]
)
def update_media(media_context, interval, filter_context, selection_context):
    filter_s = json.dumps(filter_context)
    md_dict = build_groups(
        interval, selection_context['visit'], selection_context['site_id'], filter_s)
    return [compute_output(media_context, md_dict)]
