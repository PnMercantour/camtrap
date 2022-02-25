from multiprocessing.sharedctypes import Value
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
from metadata import listSites, getVisitMetadata, groupMedia
import megaFilter
from pathlib import Path
from config import data_root

buttons = dbc.ButtonGroup([
    dbc.Button(html.I(className="fas fa-solid fa-step-backward"),
               id='media_control:first', title='Premier média du groupe'),

    dbc.Button(html.I(className="fas fa-solid fa-step-forward"),
               id='media_control:last', title='dernier média du groupe'),
])

card = dbc.Card([
    dbc.CardHeader([
        "Media",
        buttons,
    ]),
    dbc.CardBody([
        dbc.Row([
            dbc.Col("Fichier", width=2),
            dbc.Col(id='media:path'),
        ]),
        dbc.Row([
            dbc.Col("Date", width=2),
            dbc.Col(id='media:startTime'),
        ]),
        dbc.Row([
            dbc.Col("Durée", width=2),
            dbc.Col(id='media:duration'),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(html.I(className="fas fa-solid fa-backward"),
                           id='media:ctl_previous', title='Média précédent'),
                dbc.Button(html.I(className="fas fa-solid fa-forward"),
                           id='media:ctl_next', title='Média suivant'), ], width=3),
            dbc.Col(
                dcc.Slider(id="media:item", min=1, max=100, step=1, included=False, marks=None, tooltip={
                           'placement': 'bottom', 'always_visible': True},),
                width=9,
            )

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
        startTime=Output('media:startTime', 'children'),
        duration=Output('media:duration', 'children'),
    ),
    control=dict(
        disable_first=Output('media:ctl_previous', "disabled"),
        disable_last=Output('media:ctl_next', 'disabled'),
    ),
    cookie=Output('media:cookie', 'data'),
)

context = dict(
    value=Input("media:item", "value"),
    control=dict(
        previous=Input('media:ctl_previous', 'n_clicks'),
        next=Input('media:ctl_next', 'n_clicks'),
    ),
    cookie=State("media:cookie", "data"))

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
                startTime=None,
                duration=None,
            ),
            control=dict(
                disable_first=True,
                disable_last=True,
            ),
            cookie=None,
        )
    triggers = [trigger['prop_id'] for trigger in callback_context.triggered]
    media_triggers = [trigger for trigger in triggers if 'media:' in trigger]
    if len(media_triggers) > 0:
        print(media_triggers)
        trigger = media_triggers[0]
        # we don't expect multiple triggers. Process the first one
        if trigger == 'media:item.value':
            value = context["value"]
        if trigger == 'media:ctl_previous.n_clicks':
            value = context['value'] - 1
        if trigger == 'media:ctl_next.n_clicks':
            value = context['value'] + 1
        md = metadata[value - 1]
        cookie = dict(md, visit=md_dict["visit"], site_id=md_dict["site_id"])
        return dict(
            item=dict(
                value=value,
                max=no_update,
                marks=no_update,
            ),
            info=dict(
                path=md['path'],
                startTime=md['startTime'],
                duration=md['duration'],
            ),
            control=dict(
                disable_first=(value == 1),
                disable_last=(value == len(metadata)),
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

    return dict(
        item=dict(
            value=value,
            max=len(metadata),
            marks=marks,
        ),
        info=dict(
            path=md['path'],
            startTime=md['startTime'],
            duration=md['duration'],
        ),
        control=dict(
            disable_first=(value == 1),
            disable_last=(value == len(metadata)),
        ),
        cookie=cookie,
    )


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
