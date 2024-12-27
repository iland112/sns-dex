from dash import Dash, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
from dash.exceptions import PreventUpdate
from components.layouts import sidebar, youtube_main_content
import components.grids as grids
from youtube_crawl import YoutubeCrawl 

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
server = app.server

def run_crawl(query, order, category, country, language, duration):
    print(f"youtube content search spider for query={query}, order={order}, category={category}, country={country}, language={language}, videoDuration={duration} crawl started")
    crawl = YoutubeCrawl(query, order, category, country, language, duration)
    crawl.search_contents()
    
    print(f"youtube content search spider for query={query}, order={order}, category={category}, country={country}, language={language}, videoDuration={duration} crawl finished")

def get_contents_grid(conn, query, country, language, duration):
    # load data from sqlite database and create pandas dataframe
    if country != "ALL":
        contents_query = '''
            SELECT
                c.query, c.country, c.video_duration, c.published_at, c.kind, c.channel_id, c.channel_title, c.video_id, c.video_title, c.video_description,
                c.thumbnail, c.thumbnail_width, c.thumbnail_height, v.view_count, v.like_count, v.comment_count, c.inserted_at, c.updated_at
            FROM search_contents as c
            JOIN videos as v ON  c.video_id = v.video_id
            WHERE c.query = ? AND video_duration = ? and c.country = ?
            ORDER BY c.published_at DESC
        '''
        contents_df = pd.read_sql(contents_query, conn, params=(query, duration, country,))
    else:
        contents_query = '''
            SELECT
                c.query, c.country, c.video_duration, c.published_at, c.kind, c.channel_id, c.channel_title, c.video_id, c.video_title, c.video_description,
                c.thumbnail, c.thumbnail_width, c.thumbnail_height, v.view_count, v.like_count, v.comment_count, c.inserted_at, c.updated_at
            FROM search_contents as c
            JOIN videos as v ON  c.video_id = v.video_id
            WHERE c.query = ? and c.video_duration = ?
            ORDER BY c.published_at DESC
        '''
        contents_df = pd.read_sql(contents_query, conn, params=(query, duration,))

    contents_df["video"] = contents_df["video_id"] + ":" + contents_df["video_title"]
    contents_df["channel"] = contents_df["channel_id"] + ":" + contents_df["channel_title"]
    # print(contents_df.columns)

    # return youtube_content_grid(contents_df.to_dict('records'))
    return grids.youtube_content_grid(contents_df.to_dict('records'))

header = html.Div([
    html.Img(src=app.get_asset_url("SNS DeX Logo.png"), width=120, height=90, className="col-2 py-2"),
    html.H2("SNS Content Analystics", className="col-10 text-bold text-center py-4")
], className="row text-white bg-dark")

app.layout = html.Div([
    html.Div([header, sidebar, youtube_main_content], className="row")
], className="container-fluid")

@callback(
    Output("youtube-grid", "children"),
        Input("search-button", "n_clicks"),
        State("search-keyword", "value"),
        State("search-order", "value"),
        State("search-video-category", "value"),
        # State("search-channel", "value"),
        State("search-duration", "value"),
        State("search-country", "value"),
        State("search-language", "value"),
    prevent_initial_call=True,
    running=[(Output("search-button", "disabled"), True, False)]
)
def on_form_change(n_clicks, keyword_value, order_value, category_value, duration_value, country_value, language_value):
    # print(n_clicks)
    if n_clicks == 0:
        return PreventUpdate

    print(f"keyword: {keyword_value}, order: {order_value}, category: {category_value}, duration: {duration_value}, country: {country_value}, language: {language_value}")

    # load data from sqlite database and create pandas dataframe
    conn = sqlite3.connect("./data/youtube1.db")

    cursor = conn.cursor()
    # check if search_content table exists
    print('Check if search_contents table exists in the database:')
    listOfTables = cursor.execute(
        """
        SELECT name FROM sqlite_master WHERE type='table' AND name='search_contents'
        """).fetchall()

    if listOfTables == []:
        run_crawl(keyword_value, order_value, category_value, country_value, language_value, duration_value)

    count = 0
    if order_value == "relevance" and category_value == "ALL" and duration_value == "any" and country_value == "ALL":
        search_query = '''
            SELECT count(*) FROM search_contents WHERE query = ?
        '''
        count = cursor.execute(
                search_query,
            (keyword_value,)
        ).fetchone()[0]
    elif order_value != "relevance" and category_value != "ALL" and duration_value == "any" and country_value == "ALL":
        search_query = '''
            SELECT count(*) FROM search_contents WHERE query = ? AND sort = ? AND category_id = ?
        '''
        count = cursor.execute(
                search_query,
                (keyword_value, order_value, category_value,)
        ).fetchone()[0]
    elif order_value != "relevance" and category_value != "ALL" and duration_value != "any" and country_value == "ALL":
        search_query = '''
            SELECT count(*) FROM search_contents WHERE query = ? AND sort = ? AND category_id = ? AND duration = ? 
        '''
        count = cursor.execute(
                search_query,
            (keyword_value, order_value, category_value, duration_value,)
        ).fetchone()[0]
    elif order_value != "relevance" and category_value != "ALL" and duration_value != "any" and country_value != "ALL":
        search_query = '''
            SELECT count(*) FROM search_contents WHERE query = ? AND sort = ? AND category_id = ? AND duration = ? AND country = ? 
        '''
        count = cursor.execute(
                search_query,
                (keyword_value, order_value, category_value, duration_value, country_value,)
            ).fetchone()[0]

    print(f"data count : {count}")
    if count == 0:
        run_crawl(keyword_value, order_value, category_value, country_value, language_value, duration_value)

    content_grid = get_contents_grid(conn, keyword_value, country_value, language_value, duration_value)
    cursor.close()
    conn.close()
    return content_grid

if __name__ == '__main__':
    app.run(debug=True)