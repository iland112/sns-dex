import dash_bootstrap_components as dbc

def _channel_select():
    return dbc.Select(
        id="search-channel",
        options=[
            {"label": "Youtube", "value": 1},
            {"label": "Facebook", "value": 2, "disabled": True},
            {"label": "Instagram", "value": 3, "disabled": True},
            {"label": "Tiktok", "value": 4, "disabled": True},
        ],
        value=[1]
    )

def search_form():
    return dbc.Form(
    dbc.Row([
        dbc.Label("Keyword: ", width="auto"),
        dbc.Col(
            dbc.Input(id="search-keyword", type="text", placeholder="Enter keyword"),
            className="me-3",
        ),
        dbc.Label("Channel: ", width="auto"),
        dbc.Col(
            _channel_select(),
            className="me-3",
        ),
        dbc.Label("Category: ", width="auto"),
        dbc.Col(
            dbc.Input(id="search-category", type="text", placeholder="Enter keyword"),
            className="me-3",
        ),
        dbc.Label("Country: ", width="auto"),
        dbc.Col(
            dbc.Input(id="search-country", type="text", placeholder="Enter keyword"),
            className="me-3",
        ),
        dbc.Col(dbc.Button("Search", id="search-button", n_clicks=0, color="primary"), width="auto"),
    ],
    className="g-2")
)