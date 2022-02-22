import config
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback_context


from metadata import listSites, listVisits, getVisitMetadata, groupMedia


def mediaGroups(metadata, interval):
    """  Group media when end time /start time difference is smaller than interval (a number of seconds). metadata MUST be sorted by time ascending"""
    delta = timedelta(seconds=interval)
    g = None
    groups = []
    end_time = None
    for idx, media in enumerate(metadata):
        start_time = datetime.fromisoformat(media['startTime'])
        if end_time is None or end_time + delta < start_time:
            g = dict(start=idx, end=idx, startTime=media['startTime'])
            startTime = media['startTime']
            groups.append(g)
        end_time = start_time + timedelta(seconds=media['duration'])
        g['endTime'] = end_time.isoformat()
        g['end'] = idx
    return groups


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

if __name__ == '__main__':
    site = listSites()[0]
    visit = listVisits(site)[0]
    metadata = getVisitMetadata(visit, site)
    g = mediaGroups(metadata, 600)
    print(g)

    media = metadata[100]
    print(media)
    print(g[mediaGroup(media, g)])
