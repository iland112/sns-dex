from dash import Dash, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from dash.exceptions import PreventUpdate
from sqlmodel import select, Session

from components.layouts import sidebar, youtube_main_content
import components.grids as grids
from db_init import init_db, engine, search_list
from models import SearchContent, Video

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
server = app.server

def get_contents_grid(data: list):
    # load data from list of dictionary to panda dataframe
    if not data or data == []:
        return grids.youtube_content_grid([])
    
    contents_df = pd.DataFrame(data)
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

@app.callback(
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

    count = 0
    data = []
    with Session(engine) as session:
        statement = None
        if order_value == "relevance" and category_value == "ALL" and duration_value == "any" and country_value == "ALL":
            statement = select(SearchContent).where(SearchContent.query == keyword_value)
        elif order_value != "relevance" and category_value != "ALL" and duration_value == "any" and country_value == "ALL":
            statement = select(SearchContent).where(SearchContent.query == keyword_value).where(SearchContent.sort == order_value)
        elif order_value != "relevance" and category_value != "ALL" and duration_value != "any" and country_value == "ALL":
            statement = (select(SearchContent).where(SearchContent.query == keyword_value)
                        .where(SearchContent.sort == order_value)
                        .where(SearchContent.category_id == category_value)
                        .where(SearchContent.video_duration == duration_value)
                        )
        elif order_value != "relevance" and category_value != "ALL" and duration_value != "any" and country_value != "ALL":
            statement = (select(SearchContent).where(SearchContent.query == keyword_value)
                        .where(SearchContent.sort == order_value)
                        .where(SearchContent.category_id == category_value)
                        .where(SearchContent.video_duration == duration_value)
                        .where(SearchContent.country == country_value)
                        )

        results = session.exec(statement).all()
        print("results: ", results)
        count = len(results)
        print(f"data count : {len(results)}")
        data = [dict(sc) for sc in results]
        print(data)

    if count == 0:
        results = search_list(keyword_value, order_value, category_value, country_value, language_value, duration_value)
        if len(results) == 0:
            data = []
        else:
            data = [dict(sc) for sc in results]

    content_grid = get_contents_grid(data)
    return content_grid

if __name__ == '__main__':
    init_db()
    app.run(debug=True)