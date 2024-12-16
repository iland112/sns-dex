from xmlrpc.client import Fault

import dash
import json
from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3

from dash.exceptions import PreventUpdate
from scrapy.utils.log import configure_logging
from youtube_api.spiders.search import SearchSpider
from components.layouts import header, sidebar, youtube_main_content
import components.grids as grids

configure_logging()

external_css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css", ]
app = Dash(
    __name__,
    external_stylesheets=external_css,
    suppress_callback_exceptions=True,
)
server = app.server

def run_crawl(query, country):
    print(f"youtube content search spider for query={query}, country={country} crawl started")
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(SearchSpider, query, country)
    process.start()
    print(f"youtube content search spider for query={query}, country={country} crawl finished")

def get_contents_grid(conn, query, country):
    # load data from sqlite database and create pandas dataframe
    contents_query = '''
        SELECT
            c.query, c.country, c.published_at, c.kind, c.channel_id, c.channel_title, c.video_id, c.video_title, c.video_description,
            c.thumbnail, c.thumbnail_width, c.thumbnail_height, v.view_count, v.like_count, v.comment_count, c.inserted_at, c.updated_at
        FROM search_contents as c
        JOIN videos as v ON  c.video_id = v.video_id
        WHERE c.query = ? AND c.country = ?
        ORDER BY c.published_at DESC
    '''

    contents_df = pd.read_sql(contents_query, conn, params=(query, country,))
    contents_df["video"] = contents_df["video_id"] + ":" + contents_df["video_title"]
    contents_df["channel"] = contents_df["channel_id"] + ":" + contents_df["channel_title"]
    print(contents_df.columns)

    # return youtube_content_grid(contents_df.to_dict('records'))
    return grids.youtube_content_grid(contents_df.to_dict('records'))

app.layout = html.Div([
    html.Div([header, sidebar, youtube_main_content], className="row")
], className="container-fluid")

@callback(
    Output("modal-video-div", "children"),
    Input("content-grid", "cellClicked"),
    prevent_initial_call=True
)
def display_cell_clicked_on(cell):
    print(f"Clicked on cell:\n{json.dumps(cell, indent=2)}" if cell else "Click on a cell")
    video_id = cell["value"].split(":")[0]
    
    conn = sqlite3.connect('./data/youtube.db')
    
    video_query = """
        SELECT * FROM videos WHERE video_id = ?
    """
    video_df = pd.read_sql(video_query, conn, params=(video_id,))
    
    channel_query = """
        SELECT * FROM channels WHERE channel_id = ?
    """
    channel_df = pd.read_sql(channel_query, conn, params=(video_df["channel_id"][0],))
    print(channel_df["title"][0])
    
    # print(video_df["video_id"][0])
    view_count = "{:,}".format(video_df["view_count"][0])
    
    modal_body = html.Div([
        dbc.Row([html.Img(src=video_df["thumbnail"][0], width=video_df["thumbnail_width"][0], className="object-fit-contain rounded")]),
        dbc.Row([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Img(src=channel_df["thumbnail"][0], width=channel_df["thumbnail_width"][0],
                                         className="rounded-circle border img-thumbnail")
                            ], className='align-self-container'),
                            html.Div([
                                html.H4(channel_df["title"][0]),
                                html.P(f"Published_at: {channel_df['published_at'][0]}" , className="mb-0")
                            ], className="ms-3"),
                            html.Div([
                                html.H3("Subscribers"),
                                html.H2("{:,}".format(channel_df["subscriber_count"][0]), className="h1 mb-0")
                            ], className="align-self-center, ms-3")
                        ], className="d-flex flex-row")
                    ], className="d-flex justify-content-between p-md-1")
                ])
            ]),
            # dbc.Col(html.Img(src=channel_df["thumbnail"][0], width=channel_df["thumbnail_width"][0], className="rounded-circle border img-thumbnail"), width=2),
            # dbc.Col(html.Span(channel_df["title"][0])),
            # dbc.Col(
            #     dbc.Button(
            #         [
            #             "Subscriber Count ",
            #             dbc.Badge("{:,}".format(channel_df["subscriber_count"][0]))
            #         ]
            #     )
            # , width=4),
        ], align="center"),
        dbc.Row([html.H3("Statistics : ")]),
        dbc.Row([
            dbc.Col(
                dbc.Button(
                    [
                        "View Count",
                        dbc.Badge(view_count, color="light", text_color="primary", class_name="ms-1")
                    ]
                )
            ),
            dbc.Col(
                dbc.Button(
                    [
                        "Like Count",
                        dbc.Badge(video_df["like_count"], color="light", text_color="primary", class_name="ms-1")
                    ]
                )
            ),
            dbc.Col(
                dbc.Button(
                    [
                        "Comment Count",
                        dbc.Badge(video_df["comment_count"], color="light", text_color="primary", class_name="ms-1")
                    ]
                )
            ),
        ], justify="around", align="center"),
        html.Br(),
        dbc.Row([html.H3("Description : ")]),
        dbc.Row([html.P(video_df["description"][0])]),
    ], className="row ms-auto")
    
    return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(video_df["title"][0])),
            modal_body,
            dbc.ModalFooter(dbc.Button("Close", id="close", class_name="ms-auto", n_clicks=0))
        ],
        id="video-modal",
        size="lg",
        is_open=True
    )
    
@app.callback(
    Output("video-modal", "is_open"),
    [Input("close", "n_clicks")],
    [State("video-modal", "is_open")]
)
def toggle_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("youtube-grid", "children"),
        Input("search-button", "n_clicks"),
        State("search-keyword", "value"),
        State("search-channel", "value"),
        State("search-duration", "value"),
        State("search-country", "value"),
    prevent_initial_call=True,
    running=[(Output("search-button", "disabled"), True, False)]
)
def on_form_change(n_clicks, keyword_value, channel_value, category_value, country_value):
    # print(n_clicks)
    if n_clicks == 0:
        return PreventUpdate
    else:
        output =  f"keyword: {keyword_value}, channel: {channel_value} , category: {category_value}, country: {country_value}"
        print(output)
    # load data from sqlite database and create pandas dataframe
    conn = sqlite3.connect("./data/youtube.db")

    print(f"keyword: {keyword_value}, country: {country_value[0]}")
    if keyword_value and country_value:
        cursor = conn.cursor()
        # check if search_content table exists
        print('Check if search_contents table exists in the database:')
        listOfTables = cursor.execute(
            """
                SELECT name FROM sqlite_master WHERE type='table'
                AND name='search_contents'
            """).fetchall()

        if listOfTables == []:
            run_crawl(keyword_value, country_value[0])

        search_query = '''
            SELECT count(*) FROM search_contents WHERE query = ? AND country = ?
        '''
        count = cursor.execute(search_query, (keyword_value, country_value[0],)).fetchone()[0]
        print(f"data count : {count}")
        if count == 0:
            run_crawl(keyword_value, country_value[0])

        content_grid = get_contents_grid(conn, keyword_value, country_value[0])

        return content_grid


if __name__ == '__main__':
    app.run(debug=True)