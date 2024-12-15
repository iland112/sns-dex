import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

for page in dash.page_registry.values():
    print(f"page: {page}")

app.layout = html.Div([
    html.H1('SNS Dex - SNS content analystics system'),
    dash.page_container
])

if __name__ == '__main__':
    app.run(debug=True)