from dash import Dash, html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.express as px
import pandas as pd
import sqlite3

from scrapy.utils.log import configure_logging
from youtube_api.spiders.search import SearchSpider

configure_logging()

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(
    external_stylesheets=external_stylesheets
)

def run_crawl(query, country):
    print(f"youtube content search spider for query={query}, country={country} crawl started")
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(SearchSpider, query, country)
    process.start()
    print(f"youtube content search spider for query={query}, country={country} crawl finished")


def create_contents_grid(conn, query, country):
    # load data from sqlite database and create pandas dataframe
    contents_query = '''
                SELECT
                    c.query, c.country, c.published_at, c.kind, c.channel_id, c.channel_title, c.video_id, c.video_title, c.video_description,
                    c.thumbnail, c.thumbnail_width, c.thumbnail_height, v.view_count, v.like_count, v.comment_count, c.inserted_at, c.updated_at
                FROM search_contents as c
                JOIN videos as v ON  c.video_id = v.video_id
                WHERE c.query = ? AND c.country = ?
                ORDER BY c.published_at desc
            '''

    contents_df = pd.read_sql(contents_query, conn, params=(query, country,))
    # print(contents_df.columns)

    # create AG Grid component for youtube video data records
    content_columnDefs = [
        {
            "headerName": "Content Image",
            "field": "thumbnail",
            "width": 120,
            "cellRenderer": "VideoImageRenderer"
        },
        {
            "headerName": "Video Title",
            "field": "video_title",
            "wrapText": True
        },
        {
            "headerName": "Channel Title",
            "field": "channel_title"
        },
        {
            "headerName": 'Published At',
            "field": "published_at",
            "width": 120,
            "cellStyle": {'textAlign': 'center'}
            # "valueGetter": {"function": date_obj},
            # "valueFormatter": {"function": f"d3.timeFormat('%Y/%m/%d')({date_obj})"}
        },
        {
            "headerName": "View Count",
            "field": "view_count",
            "width": 120,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',')(params.value)"}
        },
        {
            "headerName": "Like Count",
            "field": "like_count",
            "width": 120,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',')(params.value)"}
        },
        {
            "headerName": "Comment Count",
            "field": "comment_count",
            "width": 120,
            "type": "rightAligned",
            "valueFormatter": {"function": "d3.format(',')(params.value)"}
        },
        {
            "headerName": 'Searched At',
            "field": "inserted_at",
            "width": 120,
            "cellStyle": {'textAlign': 'center'}
            # "valueGetter": {"function": date_obj},
            # "valueFormatter": {"function": f"d3.timeFormat('%Y/%m/%d')({date_obj})"}
        },
    ]

    content_grid = dag.AgGrid(
        id='content-grid',
        rowData=contents_df.to_dict('records'),
        columnDefs=content_columnDefs,
        dashGridOptions={'pagination': True, 'rowHeight': 90},
        columnSize="sizeToFit"
    )
    return content_grid

# Search form
channel_select = dbc.Select(
    id="search-channel",
    options=[
        {"label": "Youtube", "value": 1},
        {"label": "Facebook", "value": 2, "disabled": True},
        {"label": "Instagram", "value": 3, "disabled": True},
        {"label": "Tiktok", "value": 4, "disabled": True},
    ],
    value=[1]
)

search_form = dbc.Form(
    dbc.Row([
        dbc.Label("Keyword: ", width="auto"),
        dbc.Col(
            dbc.Input(id="search-keyword", type="text", placeholder="Enter keyword"),
            className="me-3",
        ),
        dbc.Label("Channel: ", width="auto"),
        dbc.Col(
            channel_select,
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

app.layout = html.Div([
    html.H1(children='Youtube Video Data', style={'textAlign': 'center'}),
    html.Hr(),
    search_form,
    html.P(id="form-output"),
    html.Hr(),
    dbc.Row(id="content-ag"),
], className='container h-100 d-flex flex-column')

@app.callback(
    Output("content-ag", "children"),
    [
        Input("search-keyword", "value"),
        Input("search-channel", "value"),
        Input("search-category", "value"),
        Input("search-country", "value"),
        Input("search-button", "n_clicks")
    ])
def on_form_change(keyword_value, channel_value, category_value, country_value, n_clicks):
    # print(n_clicks)
    if n_clicks == 0:
        return "Not Clicked"
    else:
        output =  f"keyword: {keyword_value}, channel: {channel_value} , category: {category_value}, country: {country_value}"
        print(output)
    # load data from sqlite database and create pandas dataframe
    conn = sqlite3.connect('./data/youtube.db')

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
            run_crawl(keyword_value, country_value)

        search_query = '''
            SELECT count(*) FROM search_contents WHERE query = ? AND country = ?
        '''
        count = cursor.execute(search_query, (keyword_value, country_value,)).fetchone()[0]
        print(f"data count : {count}")
        if count == 0:
            run_crawl(keyword_value, country_value)

        content_grid = create_contents_grid(conn, keyword_value, country_value)

        return content_grid

if __name__ == "__main__":
    app.run(debug=True)