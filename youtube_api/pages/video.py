import dash
import sqlite3
import pandas as pd
from dash import html

dash.register_page(__name__, path_template="/video/<video_id>")

def layout(video_id, **kwargs):
    conn = sqlite3.connect("./data/youtube.db")

    video_query = """
        SELECT * FROM videos WHERE video_id = ?
    """
    video_df = pd.read_sql(video_query, conn, params=(video_id,))
    print(video_df["video_id"][0])


    return html.Div([
        html.H1('Video Information page'),
        html.Img(src=video_df["thumbnail"][0]),
        html.P(video_df["title"][0]),
        html.Div([
            html.Span("View Count: "),
            html.Span(video_df["view_count"][0]),
            html.Span("Like Count: "),
            html.Span(video_df["like_count"][0]),
            html.Span("Comment Count: "),
            html.Span(video_df["comment_count"][0]),
        ]),
        html.P(video_df["description"][0]),
    ])