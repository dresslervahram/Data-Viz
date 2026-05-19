import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "iTunes Music Dashboard"

# Expose the Flask server for gunicorn (Render deployment)
server = app.server

# ── Navbar ────────────────────────────────────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            [html.I(className="bi bi-music-note-beamed me-2"), "iTunes Music Dashboard"],
            href="/", className="fw-bold fs-5"
        ),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Overview",       href="/")),
            dbc.NavItem(dbc.NavLink("Genre Explorer", href="/genres")),
            dbc.NavItem(dbc.NavLink("Release Trends", href="/trends")),
            dbc.NavItem(dbc.NavLink("Track Search",   href="/search")),
        ], navbar=True, className="ms-auto"),
    ], fluid=True),
    color="primary", dark=True, sticky="top", className="mb-0 shadow",
)

app.layout = html.Div([
    navbar,
    dbc.Container(dash.page_container, fluid=True, className="py-4"),
])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)