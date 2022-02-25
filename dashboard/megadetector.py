from dash import dcc, Input
import dash_bootstrap_components as dbc
import megadetectorData
import config
import json

with (config.project_root / "config" / "megadetector.json").open("r") as f:
    categories = json.load(f)
print(categories)

panel = [
    dbc.Label('Inclure:'),
    dcc.Dropdown(
        id="megadetector:include",
        clearable=True,
        multi=True,
        value=[1],
        placeholder='Sélectionnez ...',
        options=categories,
    ),
    dbc.Label('Seuil de détection'),
    dcc.Slider(
        id='megadetector:in_threshold',
        min=0,
        max=1,
        step=0.02,
        marks=None,
        value=0.96,
        tooltip={'placement': 'bottom', 'always_visible': True},
    ),

    dbc.Label('Exclure:'),
    dcc.Dropdown(
        id="megadetector:exclude",
        clearable=True,
        multi=True,
        value=[2, 3],
        placeholder='Sélectionnez ...',
        options=categories,
    ),
    dbc.Label('Seuil de détection'),
    dcc.Slider(
        id='megadetector:out_threshold',
        min=0,
        max=1,
        marks=None,
        step=0.02,
        value=0.80,
        tooltip={'placement': 'bottom', 'always_visible': True},
    ),
]
parameters = dict(
    include=Input('megadetector:include', 'value'),
    in_threshold=Input('megadetector:in_threshold', 'value'),
    exclude=Input('megadetector:exclude', 'value'),
    out_threshold=Input('megadetector:out_threshold', 'value'),
)


def filter(metadata, parameters, visit, site_id):
    # WARNING : category comes as an int and has to be coerced to a string.
    def include_test(value):
        return any([(value.get(str(i), 0) >= parameters["in_threshold"]) for i in parameters['include']])

    def exclude_test(value):
        return all([value.get(str(i), 0) < parameters["out_threshold"]for i in parameters['exclude']])

    megadetector_data = megadetectorData.getVisitData(visit, site_id)
    result = [md for md in metadata for (name, value) in megadetector_data.items() if md['fileName'] == name and include_test(
        value) and exclude_test(value)]
    return result
