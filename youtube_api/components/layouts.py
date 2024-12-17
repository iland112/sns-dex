from dash import html
import dash_bootstrap_components as dbc
import pandas as pd

header = html.Div([
    html.H1("SNS Dex")    
], className="row")

channel_dropdown = dbc.Select(
    id="search-channel",
    options=[
        {"label": "Youtube", "value": 1},
        {"label": "Facebook", "value": 2, "disabled": True},
        {"label": "Instagram", "value": 3, "disabled": True},
        {"label": "Tiktok", "value": 4, "disabled": True},
    ],
    value=[1],
    className="text-dark p-2"
)

country_codes_df = pd.read_csv("./data/country_codes.csv")
# print([{ "label": row['name'], "value": row['alpha-2'] } for index, row in country_codes_df.iterrows()])

country_dropdown = dbc.Select(
    id="search-country",
    options=[
        { "label": row['name'], "value": row['alpha-2'] } for index, row in country_codes_df.iterrows()
    ],
    value=["VN"],
    className="text-dark p-2"
)

duration_dropdown = dbc.Select(
    id="search-duration",
    options=[
        {"label": "Any", "value": "any"},
        {"label": "Long", "value": "long"},
        {"label": "Medium", "value": "medium"},
        {"label": "Short", "value": "short"},
    ],
    value=["any"],
    className="text-dark p-2"
)

keyword_input = dbc.InputGroup([
    dbc.Col(dbc.Input(id="search-keyword", type="text", className="text-dark p-2")),
    dbc.Col(dbc.Button("Search", id="search-button", n_clicks=0, color="primary", class_name="ms-1"))   
])

sidebar = html.Div([
    html.Br(),
    html.H3("Search Data", className="text-center fw-bold fs-2"),
    html.Br(),
    html.H5("Keyword", className="fs-4"),
    keyword_input,
    html.Br(),
    html.H5("Channel", className="fs-4"),
    channel_dropdown,
    html.Br(),
    html.H5("Country", className="fs-4"),
    country_dropdown,
    html.Br(),
    html.H5("Video Duration", className="fs-4"),
    duration_dropdown,
], className="col-2 bg-dark text-white", style={"height": "100vh"})

youtube_main_content = html.Div([
    html.Div(id="youtube-grid", style={"height": "80vh"}),
    html.Div(id="modal-video-div", style={"height": "20vh"}),  
], className="col-10", style={"height": "100vh"})