import config
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html, Input, Output, State, callback_context


from metadata import listSites, listVisits, getVisitMetadata, groupMedia


def mediaGroup(media, groups):
    "media is a media metadata, groups structure is as returned by groupMedia"
    startTime = media['startTime']
    for idx, group in enumerate(groups):
        if startTime >= group['startTime'] and startTime <= group['endTime']:
            return idx
    raise ValueError(media)


buttons = dbc.ButtonGroup([
    dbc.Button(html.I(className="fas fa-solid fa-fast-backward"),
               id='group_control:previous', title='Groupe précédent'),
    dbc.Button(html.I(className="fas fa-solid fa-fast-forward"),
               id='group_control:next', title='Groupe suivant'),
])

group_card = dbc.Card([
    dbc.CardHeader(["Groupe", buttons]),
    dbc.CardBody([
        dcc.Dropdown(id='group:select', clearable=False, options=[]),
        dbc.Label('Intervalle (secondes)'),
        dcc.Slider(
            id='group:interval',
            min=0,
            max=600,
            step=10,
            marks=None,
            value=300,
            tooltip={'placement': 'bottom', 'always_visible': True},
        ),
    ]),
])


# @ dash.callback(
#     Output('group:select', 'options'),
#     Output('group:select', 'value'),
#     Input('group:interval', 'value'),
#     Input('select:visit', 'value'),
#     State('select:site', 'value'),
#     State('group:select', 'options'),
#     State('group:select', 'value'),
#     State('prefs:group_media', 'value'),
#     Input('group_control:previous', 'n_clicks'),
#     Input('group_control:next', 'n_clicks'),
#     # Input('group_control:first', 'n_clicks'),
#     # Input('group_control:last', 'n_clicks'),
# )
# def update_group_dropdown(interval, date, site_id, options, value, group_media, _1, _2):
#     changed_id = [p['prop_id'] for p in callback_context.triggered][0]
#     if 'group_media' in changed_id or 'group:interval' in changed_id:
#         if group_media:
#             groups = groupMedia(getVisitMetadata(
#                 date, site_id), interval)
#             # TODO passer les metadonnées du media
#             current_group = group_of_media(groups, None)
#             return [options, current_group]
#         elif 'group:interval' in changed_id:
#             groups = groupMedia(getVisitMetadata(
#                 date, site_id), interval)
#             return [groups, None]
#         else:
#             return [options, None]
#     if 'select:visit' in changed_id:
#         groups = groupMedia(getVisitMetadata(
#             date, site_id), interval)
#         options = [{
#             'label': f"{group['startTime']} ({len(group['metadata'])})",
#             'value': group['startTime']
#         } for group in groups]
#         value = groups[0]['startTime'] if len(
#             groups) > 0 and group_media else None
#         return [options, value]
#     values = [item['value'] for item in options]
#     if len(values) == 0:
#         return [no_update, no_update]
#     if 'group_control' in changed_id:
#         if value is None:
#             # TODO mettre en cache les metadonnées du groupe
#             groups = groupMedia(getVisitMetadata(
#                 date, site_id), interval)
#             # TODO passer les metadonnées du media
#             value = group_of_media(groups, None)
#         if 'first' in changed_id:
#             return [no_update, values[0]]
#         if 'last' in changed_id:
#             return [no_update, values[-1]]
#         if 'previous' in changed_id:
#             return [no_update, values[max(values.index(value) - 1, 0)]]
#         if 'next' in changed_id:
#             return [no_update, values[min(values.index(value) + 1, len(values) - 1)]]
#     else:
#         return [no_update, no_update]


if __name__ == '__main__':
    site = listSites()[0]
    visit = listVisits(site)[0]
    metadata = getVisitMetadata(visit, site)
    g = mediaGroups(metadata, 600)
    print(g)

    media = metadata[100]
    print(media)
    print(g[mediaGroup(media, g)])
