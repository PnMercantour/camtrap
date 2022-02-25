import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback_context
from metadata import listSites, getVisitMetadata, groupMedia
import megaFilter
from pathlib import Path
from config import data_root

buttons = dbc.ButtonGroup([
    dbc.Button(html.I(className="fas fa-solid fa-step-backward"),
               id='media_control:first', title='Premier média du groupe'),
    dbc.Button(html.I(className="fas fa-solid fa-backward"),
               id='media_control:previous', title='Média précédent'),
    dbc.Button(html.I(className="fas fa-solid fa-forward"),
               id='media_control:next', title='Média suivant'),
    dbc.Button(html.I(className="fas fa-solid fa-step-forward"),
               id='media_control:last', title='dernier média du groupe'),
])

card = dbc.Card([
    dbc.CardHeader([
        "Media",
        buttons,
    ]),
    dbc.CardBody([
        dbc.Label('Media', id='media_count'),
        dcc.Slider(min=1, max=100, step=1, marks={
                   1: '1', 100: '100'}, included=False),
        dcc.Dropdown(
            id='select:media',
            clearable=False,
            options=[]
        ),
        dcc.Store(id='media:cookie')
    ])
])

o_media_options = (Output('select:media', 'options'),
                   Output('select:media', 'value'),
                   Output('media_count', 'children'))


def to_media_options(md_dict):
    return ([{'label': media['startTime'], 'value': media['path']}
            for media in md_dict['filtered']],
            md_dict['filtered'][0]['path'] if len(
                md_dict['filtered']) > 0 else None,
            f"Media [{len(md_dict['filtered'])}/{len(md_dict['raw'])}]")


context = dict(path=Input('select:media', 'value'), controls=(Input("media_control:first", 'n_clicks'), Input("media_control: previous", 'n_clicks'), Input('media_control:next', 'n_clicks'),
                                                              Input('media_control:last', 'n_clicks')))


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
