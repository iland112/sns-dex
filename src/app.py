from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3

from dash.exceptions import PreventUpdate
from scrapy.utils.log import configure_logging


configure_logging()

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)
server = app.server

