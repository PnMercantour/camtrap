# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from skimage import data

img = data.chelsea()
fig = px.imshow(img)
fig.update_layout(dragmode="drawrect")
config = {}

app = dash.Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

datafig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='Camtrap Dashboard'),

    html.Div(children='''
        Présentation et classification des données issues des pièges photo du Parc national du Mercantour.
    '''),
    html.Div(children=[
        html.H3("Image sélectionnée"),
        dcc.Graph(figure=fig, config=config)]),
    dcc.Graph(
        id='example-graph',
        figure=datafig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
