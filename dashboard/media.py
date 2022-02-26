from multiprocessing.sharedctypes import Value
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
from datetime import datetime, timedelta
import json
from metadata import listSites, getVisitMetadata, groupMedia
import selection
import filter
from functools import lru_cache
from pathlib import Path
from config import data_root


prev_button = dbc.Button(html.I(className="fas fa-solid fa-step-backward"),
                         id='media:ctl_previous', title='Média précédent')

next_button = dbc.Button(html.I(className="fas fa-solid fa-step-forward"),
                         id='media:ctl_next', title='Média suivant')

item_slider = dcc.Slider(id="media:item", min=1, max=100, step=1, included=False, marks=None, tooltip={
    'placement': 'bottom', 'always_visible': True},)

first_in_group_button = dbc.Button(html.I(className="fas fa-solid fa-backward"),
                                   id='media:ctl_first', title='Premier média du groupe')

last_in_group_button = dbc.Button(html.I(className="fas fa-solid fa-forward"),
                                  id='media:ctl_last', title='Dernier média du groupe')

in_group_slider = dcc.Slider(id="media:zoom_item", min=1, max=100, step=1, included=False, marks=None, tooltip={
    'placement': 'bottom', 'always_visible': True},)

prev_group_button = dbc.Button(html.I(className="fas fa-solid fa-fast-backward"),
                               id='media_group:ctl_previous', title='Premier média du groupe précédent')

next_group_button = dbc.Button(html.I(className="fas fa-solid fa-fast-forward"),
                               id='media_group:ctl_next', title='Premier média du groupe suivant')

group_slider = dcc.Slider(id="media_group:item", min=1, max=100, step=1, included=False, marks=None, tooltip={
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
        {'label': '3h', 'value': 10800}
    ],
)

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
            dbc.Col("Médias du groupe", width=3),
            dbc.Tooltip("Durée du groupe de médias",
                        target='media_group:duration'),
            dbc.Col(id='media_group:duration'),
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
    item=dict(
        value=Output('media:item', 'value'),
        max=Output('media:item', 'max'),
        marks=Output('media:item', 'marks'),
    ),
    info=dict(
        path=Output('media:path', 'children'),
        fileName=Output('media:fileName', 'children'),
        startTime=Output('media:startTime', 'children'),
        duration=Output('media:duration', 'children'),
    ),
    control=dict(
        disable_previous=Output('media:ctl_previous', "disabled"),
        disable_next=Output('media:ctl_next', 'disabled'),
        disable_first=Output('media:ctl_first', 'disabled'),
        disable_last=Output('media:ctl_last', 'disabled'),
    ),
    zoom_item=dict(
        value=Output('media:zoom_item', 'value'),
        min=Output('media:zoom_item', 'min'),
        max=Output('media:zoom_item', 'max'),
        marks=Output('media:zoom_item', 'marks'),
    ),
    cookie=Output('media:cookie', 'data'),
)


context = dict(
    value=Input("media:item", "value"),
    control=dict(
        previous=Input('media:ctl_previous', 'n_clicks'),
        next=Input('media:ctl_next', 'n_clicks'),
        first=Input('media:ctl_first', 'n_clicks'),
        last=Input('media:ctl_last', 'n_clicks'),
    ),
    zoom_item=dict(
        min=State('media:zoom_item', 'min'),
        max=State('media:zoom_item', 'max'),
    ),
    cookie=State("media:cookie", "data"))

interval = Input('media_group:interval', 'value')
path = Input('media:path', 'children')


def compute_output(context, md_dict):
    metadata = md_dict['metadata']
    if metadata is None or len(metadata) == 0:
        return dict(
            item=dict(
                value=None,
                max=no_update,
                marks=None,
            ),
            info=dict(
                path=None,
                fileName=None,
                startTime=None,
                duration=None,
            ),
            control=dict(
                disable_previous=True,
                disable_next=True,
                disable_first=True,
                disable_last=True,
            ),
            zoom_item=dict(
                value=None,
                min=None,
                max=None,
                marks=None
            ),
            cookie=None,
        )

    def first_item_of_group():
        result = context['zoom_item']['min']
        print('first in group', result)
        return result

    def last_item_of_group():
        result = context['zoom_item']['max']
        print('last in group', result)
        return result

    def find_group(item):
        groups = md_dict['groups']
        md_idx = item - 1
        print('find group')
        for idx, group in enumerate(groups):
            if group["start"] <= md_idx and group["end"] >= md_idx:
                return idx + 1, group["start"] + 1, group["end"] + 1
        raise ValueError((groups, item))

    triggers = [trigger['prop_id'] for trigger in callback_context.triggered]
    media_triggers = [trigger for trigger in triggers if 'media:' in trigger]
    if len(media_triggers) > 0:
        print(media_triggers)
        trigger = media_triggers[0]
        # we don't expect multiple triggers. Process the first one
        if trigger == 'media:ctl_first.n_clicks':
            value = first_item_of_group()
            group_update = False
        elif trigger == 'media:ctl_last.n_clicks':
            value = last_item_of_group()
            group_update = False
        elif trigger == 'media:zoom_item.value':
            value = context["zoom_value"]
            group_update = False
        elif trigger == 'media:item.value':
            value = context["value"]
            group_update = True
        elif trigger == 'media:ctl_previous.n_clicks':
            value = context['value'] - 1
            group_update = True
        elif trigger == 'media:ctl_next.n_clicks':
            value = context['value'] + 1
            group_update = True
        else:
            print('Unhandled trigger', trigger)
            # reset to stable values
            value = 1
            group_update = True
        md = metadata[value - 1]
        if group_update:
            print('group update', value)
            (group_value, zoom_min, zoom_max) = find_group(value)
            zoom_marks = {}
            zoom_marks[zoom_max] = str(zoom_max)
        else:
            zoom_min = no_update
            zoom_max = no_update
            zoom_marks = no_update
        cookie = dict(md, visit=md_dict["visit"], site_id=md_dict["site_id"])
        return dict(
            item=dict(
                value=value,
                max=no_update,
                marks=no_update,
            ),
            info=dict(
                path=md['path'],
                fileName=md['fileName'],
                startTime=md['startTime'],
                duration=md['duration'],
            ),
            control=dict(
                disable_previous=(value == 1),
                disable_next=(value == len(metadata)),
                disable_first=(value == zoom_min),
                disable_last=(value == zoom_max),
            ),
            zoom_item=dict(
                value=value,
                min=zoom_min,
                max=zoom_max,
                marks=zoom_marks,
            ),
            cookie=cookie,
        )
    # not a media trigger, find the closest item if still on the same visit
    print('context', context)
    old_cookie = context['cookie']
    if old_cookie is not None:
        if md_dict['visit'] == old_cookie.get("visit") and md_dict['site_id'] == old_cookie.get('site_id'):
            print('match____________')
            for idx, md in enumerate(metadata):
                value = idx + 1
                if md['fileName'] == old_cookie['fileName']:
                    break
                if md['startTime'] > old_cookie['startTime']:
                    break
            else:
                value = 1
        else:
            print('no match')
            value = 1
    else:
        value = 1
    md = metadata[value - 1]
    marks = {}
    marks[len(metadata)] = str(len(metadata))
    cookie = dict(md, visit=md_dict["visit"], site_id=md_dict["site_id"])
    (group_value, zoom_min, zoom_max) = find_group(value)
    zoom_marks = {}
    zoom_marks[zoom_max] = str(zoom_max)
    return dict(
        item=dict(
            value=value,
            max=len(metadata),
            marks=marks,
        ),
        info=dict(
            path=md['path'],
            fileName=md['fileName'],
            startTime=md['startTime'],
            duration=md['duration'],
        ),
        control=dict(
            disable_previous=(value == 1),
            disable_next=(value == len(metadata)),
            disable_first=(value == zoom_min),
            disable_last=(value == zoom_max),
        ),
        zoom_item=dict(
            value=value,
            min=zoom_min,
            max=zoom_max,
            marks=zoom_marks,
        ),
        cookie=cookie,
    )


def groupMedias(metadata, interval):
    """  Group medias when end time /start time difference is smaller than interval (a number of seconds). metadata MUST be sorted by time ascending"""
    delta = timedelta(seconds=interval)
    g = None
    groups = []
    end_time = None
    for idx, md in enumerate(metadata):
        start_time = datetime.fromisoformat(md['startTime'])
        if end_time is None or end_time + delta < start_time:
            g = dict(start=idx, end=idx, startTime=md['startTime'])
            groups.append(g)
        end_time = start_time + timedelta(seconds=md['duration'])
        g['endTime'] = end_time.isoformat()
        g['end'] = idx
    return groups


@ lru_cache
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
        context,
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


# @ dash.callback(
#     Output('select:media', 'options'),
#     Output('file_info', 'children'),
#     Input('group:select', 'value'),
#     Input('select:visit', 'value'),
#     State('group:interval', 'value'),
#     State('select:site', 'value'),
#     Input('detection:source', 'value'),
#     Input('detection:megadetector', 'value'),
#     Input('detection:megadetector:in_threshold', 'value'),
#     Input('detection:megadetector:out_threshold', 'value')
# )
# def update_media_dropdown(group_start_time, visit, interval, site_id, source, megadetector, in_threshold, out_threshold):
#     "triggered by detection filter"
#     media_metadata = getVisitMetadata(visit, site_id)
#     if group_start_time is not None:
#         groups = groupMedia(media_metadata, interval)
#         selected_group = next(
#             (group for group in groups if group['startTime'] == group_start_time), None)
#         full_media_options = [{'label': media['startTime'], 'value': media['path']}
#                               for media in selected_group['metadata']]
#     else:
#         full_media_options = [{'label': media['startTime'],
#                                'value': media['path']} for media in media_metadata]

#     if source == 'all':
#         return [full_media_options, f'{len(full_media_options)} vidéos']

#     if source == 'megadetector':
#         if megadetector == 'all':
#             l = megaFilter.processed(
#                 data_root / 'detection'/'visits', site_id, visit)
#             options = [option for option in full_media_options if Path(
#                 option['value']).name in l]
#             return [options, f'{len(options)} vidéos analysées sur {len(full_media_options)}']
#         if megadetector in ['pass', 'reject']:
#             l_pass, l_rejected = megaFilter.filter(
#                 data_root / 'detection' / 'visits', site_id, visit, in_threshold, out_threshold)
#             video_count = len(full_media_options)
#             if megadetector == 'pass':
#                 l_out = l_pass
#                 message = 'vidéos retenues'
#             else:
#                 l_out = l_rejected
#                 message = 'vidéos rejetées'
#             options = [option for option in full_media_options if Path(
#                 option['value']).name in l_out]
#             return [options, f'{len(options)} {message} sur {len(full_media_options)}']
#     print('something wrong with source', source, megadetector)
#     raise ValueError(source)


# @ dash.callback(
#     Output('select:media', 'value'),
#     Input('select:media', 'options'),
#     State('select:media', 'value'),
#     State('select:visit', 'value'),
#     State('select:site', 'value'),
#     Input('media_control:first', 'n_clicks'),
#     Input('media_control:previous', 'n_clicks'),
#     Input('media_control:next', 'n_clicks'),
#     Input('media_control:last', 'n_clicks'),
# )
# def set_media(options, value, visit, site_id, first, previous, next, last):
#     if options is None or len(options) == 0:
#         return None
#     changed_id = [p['prop_id'] for p in callback_context.triggered][0]
#     if 'media_control:first' in changed_id:
#         return options[0]['value']
#     if 'media_control:next' in changed_id:
#         values = [item['value'] for item in options]
#         return values[min(values.index(value) + 1, len(values) - 1)]
#     if 'media_control:previous' in changed_id:
#         values = [item['value'] for item in options]
#         return values[max(values.index(value) - 1, 0)]
#     if 'media_control:last' in changed_id:
#         return options[-1]['value']
#     return options[0]['value']
