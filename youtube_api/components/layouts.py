import dash
import requests
import datetime
from dash import html, Input, Output, callback, State
import dash_bootstrap_components as dbc
import pandas as pd
import json
import sqlite3

from scrapy.utils.project import get_project_settings

# header = html.Div([
#     html.Img(src=dash.get_app().get_asset_url("SNS DeX Logo.png"))
# ], className="row")

channel_dropdown = dbc.Select(
    id="search-channel",
    options=[
        {"label": "Youtube", "value": 1},
        {"label": "Facebook", "value": 2, "disabled": True},
        {"label": "Instagram", "value": 3, "disabled": True},
        {"label": "Tiktok", "value": 4, "disabled": True},
    ],
    value=1,
    className="text-dark p-2"
)

def table_exists(cursor, table_name):
    listOfTables = cursor.execute(
        """
            SELECT name FROM sqlite_master WHERE type='table'
            AND name= ?
        """, (table_name,)).fetchall()
    if listOfTables == []:
        return False
    else:
        return True

def languages_dropdown():
    conn = sqlite3.connect("./data/youtube1.db")
    cursor = conn.cursor()

    if not table_exists(cursor, "language_codes"):
        language_ddl = """
            CREATE TABLE IF NOT EXISTS i18n_language_codes(
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                inserted_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
        cursor.execute(language_ddl)

        params = {
            'key': get_project_settings().get("YOUTUBE_API_KEY"),
            'part': 'snippet',
        }
        url = f"https://youtube.googleapis.com/youtube/v3/i18nLanguages?"
        response = requests.get(url, params)
        items = response.json()["items"]
        for item in items:
            snippet = item["snippet"]
            search_query = """
                SELECT count(*) FROM i18n_language_codes WHERE code = ? AND name = ?
            """
            count = cursor.execute(search_query, (snippet["hl"], snippet["name"])).fetchone()[0]
            if count == 0:
                insert_query = """
                    INSERT INTO i18n_language_codes (code, name, inserted_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """
                inserted_at = datetime.datetime.now()
                cursor.execute(insert_query, (snippet["hl"], snippet["name"], inserted_at, inserted_at))
                conn.commit()

    languages_df = pd.read_sql("""SELECT * FROM i18n_language_codes""", conn)
    conn.close()

    return dbc.Select(
        id="search-language",
        options=[{"label": "--ALL--", "value": "ALL"}] + [
            {"label": row["name"], "value": row["code"]} for index, row in languages_df.iterrows()
        ],
        value = "ALL",
        className = "text-dark p-2"
    )

def countries_dropdown():
    conn = sqlite3.connect("./data/youtube1.db")
    cursor = conn.cursor()

    if not table_exists(cursor, "i18n_region_codes"):
        language_ddl = """
            CREATE TABLE IF NOT EXISTS i18n_region_codes(
                id INTEGER PRIMARY KEY,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                inserted_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
        cursor.execute(language_ddl)

        params = {
            'key': get_project_settings().get("YOUTUBE_API_KEY"),
            'part': 'snippet',
        }
        url = f"https://www.googleapis.com/youtube/v3/i18nRegions?"
        response = requests.get(url, params)
        items = response.json()["items"]
        for item in items:
            snippet = item["snippet"]
            search_query = """
                SELECT count(*) FROM i18n_region_codes WHERE code = ? AND name = ?
            """
            count = cursor.execute(search_query, (snippet["gl"], snippet["name"])).fetchone()[0]
            if count == 0:
                insert_query = """
                    INSERT INTO i18n_region_codes (code, name, inserted_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """
                inserted_at = datetime.datetime.now()
                cursor.execute(insert_query, (snippet["gl"], snippet["name"], inserted_at, inserted_at))
                conn.commit()

        cursor.close()
    regions_df = pd.read_sql("""SELECT * FROM i18n_region_codes ORDER BY code""", conn)


    return dbc.Select(
        id="search-country",
        options=[{"label": "--ALL--", "value": "ALL"}] + [
            {"label": row["name"], "value": row["code"]} for index, row in regions_df.iterrows()
        ],
        value = "ALL",
        className = "text-dark p-2"
    )

def video_category_dropdown():
    conn = sqlite3.connect("./data/youtube1.db")
    cursor = conn.cursor()

    if not table_exists(cursor, "video_category_codes"):
        language_ddl = """
            CREATE TABLE IF NOT EXISTS video_category_codes(
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                inserted_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
        cursor.execute(language_ddl)

        params = {
            'key': get_project_settings().get("YOUTUBE_API_KEY"),
            'part': 'snippet',
            'regionCode': 'US'
        }
        url = f"https://www.googleapis.com/youtube/v3/videoCategories?"
        response = requests.get(url, params)
        items = response.json()["items"]
        for item in items:
            snippet = item["snippet"]
            search_query = """
                SELECT count(*) FROM video_category_codes WHERE id = ? AND title = ?
            """
            count = cursor.execute(search_query, (item["id"], snippet["title"])).fetchone()[0]
            if count == 0:
                insert_query = """
                    INSERT INTO video_category_codes (id, title, channel_id, inserted_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """
                inserted_at = datetime.datetime.now()
                cursor.execute(insert_query, (item["id"], snippet["title"], snippet["channelId"], inserted_at, inserted_at))
                conn.commit()
        cursor.close()

    categories_df = pd.read_sql("""SELECT * FROM video_category_codes ORDER BY title""", conn)

    return dbc.Select(
        id="search-video-category",
        options=[{"label": "--ALL--", "value": "ALL"}] + [
            {"label": row["title"], "value": row["id"]} for index, row in categories_df .iterrows()
        ],
        value = "ALL",
        className = "text-dark p-2"
    )

order_dropdown = dbc.Select(
    id="search-order",
    options=[
        {"label": "Newest", "value": "date"},
        {"label": "Rating", "value": "rating"},
        {"label": "Relevance", "value": "relevance"},
        {"label": "Title", "value": "title"},
        {"label": "Video Count", "value": "videoCount"},
        {"label": "View Count", "value": "viewCount"},
    ],
    value="relevance",
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
    value="any",
    className="text-dark p-2"
)

keyword_input = dbc.InputGroup([
    dbc.Col(dbc.Input(id="search-keyword", type="text", className="text-dark p-2"), align="center", width=8),
    dbc.Col(dbc.Button("Search", id="search-button", n_clicks=0, color="primary", class_name="ms-4"), align="center", width=2)
])

sidebar = html.Div([
    html.Br(),
    html.H3("Search Conditions", className="text-center fw-bold"),
    html.Br(),
    html.H5("Channel", className="fs-4"),
    channel_dropdown,
    html.Br(),
    html.H5("Keyword :", className="fs-4"),
    keyword_input,
    html.Br(),
    html.H5("Order By :", className="fs-4"),
    order_dropdown,
    html.Br(),
    html.H5("Category :", className="fs-4"),
    video_category_dropdown(),
    html.Br(),
    html.H5("Country :", className="fs-4"),
    countries_dropdown(),
    # html.Br(),
    # html.H5("Language", className="fs-4"),
    # languages_dropdown(),
    html.Br(),
    html.H5("Video Duration:", className="fs-4"),
    duration_dropdown,
], className="col-2 bg-dark text-white", style={"height": "100vh"})

default_main_content_children = html.Div(
    html.H1("Please input keyword and click search button for display content list"),
    className="text-center py-auto"
)

youtube_main_content = html.Div([
    html.Div(id="youtube-grid", style={"height": "80vh"}, children=default_main_content_children),
    html.Div(id="modal-video-div", style={"height": "20vh"}),  
], className="col-10", style={"height": "100vh"})

def stat_card(icon: str, count: int, text: str):
    formatted_count = "{:,}".format(count)
    return dbc.Card([
        dbc.Row(
            [
                dbc.Col(html.H1(html.I(className= icon + " m-2")), class_name="col-3"),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H3(formatted_count, className="card-text"),
                            html.Small(text, className="card-text")
                        ]
                    )
                , class_name="col-9"),
            ]
            , className="g-0 d-flex align-items-center"
        ),
    ], outline=False)

def channel_card(df):
    return dbc.Card(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Img(
                                        src=df["thumbnail"][0],
                                        className="rounded-circle border bor-2 border-danger img-thumbnail"
                                    ),
                                    class_name="col-2"
                                ),
                                dbc.Col(
                                    [
                                        html.H4(df["title"][0]),
                                        html.P(f"Published_at: {df['published_at'][0]}")
                                    ],
                                    class_name="col-10"
                                ),
                            ],
                            class_name="d-flex align-items-center"
                        ),
                        class_name="col-8"
                    ),
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(html.H1(html.I(className="bi bi-people")), class_name="col-2"),
                                dbc.Col([
                                    html.H3("{:,}".format(df["subscriber_count"][0])),
                                    html.H5("Subscribers")
                                ], className="ms-2 col-8")
                            ],
                            class_name="d-flex align-items-center"
                        ),
                        class_name="col-4"
                    )
                ],
                className="d-flex justify-content-around align-items-center"
            ),
        ],
    )

@callback(
    Output("modal-video-div", "children"),
    Input("content-grid", "selectedRows"),
    prevent_initial_call=False
)
def display_cell_clicked_on(rows):
    print(rows)
    if len(rows) == 0:
        return ""

    # print(f"Clicked on cell:\n{json.dumps(cell, indent=2)}" if cell else "Click on a cell")
    video_id = rows[0]["video_id"]

    conn = sqlite3.connect('./data/youtube1.db')

    video_query = """
        SELECT * FROM videos WHERE video_id = ?
    """
    video_df = pd.read_sql(video_query, conn, params=(video_id,))

    channel_query = """
        SELECT * FROM channels WHERE channel_id = ?
    """
    channel_df = pd.read_sql(channel_query, conn, params=(video_df["channel_id"][0],))
    # print(channel_df["title"][0])

    print(video_df["video_id"][0])
    #view_count = "{:,}".format(video_df["view_count"][0])

    modal_body = html.Div(
        [
            # video statistics
            dbc.Row(
                [
                    dbc.Col(
                        stat_card("bi bi-eye", video_df["view_count"][0], "Views")
                    ),
                    dbc.Col(
                        stat_card("bi bi-hand-thumbs-up", video_df["like_count"][0], "Likes")
                    ),
                    dbc.Col(
                        stat_card("bi bi-chat-left-text", video_df["comment_count"][0], "Comments"),
                    ),
                ],
                justify="around",
                align="center",
                class_name="m-2"
            ),
            # channel info
            dbc.Row(
                [
                    channel_card(channel_df),
                ],
                class_name="m-2"
            ),
            # video description
            dbc.Card(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Img(
                                src=video_df["thumbnail"][0],
                                # width=video_df["thumbnail_width"][0],
                                className="img-fluid rounded-start"
                            ),
                            class_name='col-md-4'
                        ),
                        dbc.Col(
                            dbc.CardBody(
                                [
                                    html.H3("Video Description : "),
                                    html.P(video_df["description"][0])
                                ]
                            ),
                            class_name="col-md-8"
                        )
                    ],
                    className="row g-0"
                ),
                class_name="m-2"
            ),
        ]
    )

    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(video_df["title"][0])),
        modal_body,
        dbc.ModalFooter(dbc.Button("Close", id="close", class_name="ms-auto", n_clicks=0))
    ],
        id="video-modal",
        size="lg",
        is_open=True
    )

@callback(
    Output("video-modal", "is_open"),
    [Input("close", "n_clicks")],
    [State("video-modal", "is_open")]
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open