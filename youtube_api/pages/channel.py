import dash
import sqlite3
import pandas as pd
from dash import html

dash.register_page(__name__, path_template="/channel/<channel_id>")

def layout(channel_id=None, **kwargs):
    conn = sqlite3.connect("./data/youtube.db")

    channel_query = """
            SELECT * FROM channels WHERE channel_id = ?
        """
    channel_df = pd.read_sql(channel_query, conn, params=(channel_id,))
    # print(channel_df["title"][0])

    return html.Div([
        html.H1('Channel Information page'),
        html.Img(src=channel_df["thumbnail"][0]),
        html.P(channel_df["title"][0]),
        html.Div([
            html.Span("View Count: "),
            html.Span(channel_df["view_count"][0]),
            html.Span("Subscriber Count: "),
            html.Span(channel_df["subscriber_count"][0]),
            html.Span("Video Count: "),
            html.Span(channel_df["video_count"][0]),
        ]),
        html.P(channel_df["description"][0]),
    ])