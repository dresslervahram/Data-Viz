import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from data import df

dash.register_page(__name__, path="/search", name="Track Search")

ALL_GENRES = sorted(df["genre"].unique())

layout = html.Div([
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.B("Search & Filter")),
            dbc.CardBody([
                dbc.InputGroup([
                    dbc.Input(id="s-query", placeholder="Artist or track name…", debounce=True),
                    dbc.Button("Search", id="s-btn", color="primary", n_clicks=0),
                ], className="mb-3"),
                html.Label("Genre", className="fw-semibold small mb-1"),
                dcc.Dropdown(
                    id="s-genre",
                    options=[{"label": "All", "value": "ALL"}] +
                            [{"label": g, "value": g} for g in ALL_GENRES],
                    value="ALL", clearable=False, className="mb-3",
                ),
                html.Label("Price Range ($)", className="fw-semibold small mb-1"),
                dcc.RangeSlider(id="s-price", min=0.69, max=1.29, step=0.30,
                                value=[0.69, 1.29],
                                marks={0.69: "$0.69", 0.99: "$0.99", 1.29: "$1.29"},
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-3"),
                html.Label("Max Duration (min)", className="fw-semibold small mb-1"),
                dcc.Slider(id="s-dur", min=1, max=15, step=1, value=10,
                           marks={1: "1", 5: "5", 10: "10", 15: "15"},
                           tooltip={"placement": "bottom", "always_visible": True},
                           className="mb-3"),
                dbc.Button("Reset", id="s-reset", color="secondary",
                           outline=True, size="sm", n_clicks=0),
            ]),
        ], className="shadow-sm border-0", style={"position": "sticky", "top": "70px"}), md=3),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.B("Results "),
                    dbc.Badge("—", id="s-count", color="primary", pill=True),
                ]),
                dbc.CardBody(html.Div(id="s-table")),
            ], className="shadow-sm border-0 mb-3"),
            dbc.Card([
                dbc.CardHeader(html.B("Genre Breakdown of Results")),
                dbc.CardBody(dcc.Graph(id="s-chart", config={"displayModeBar": False})),
            ], className="shadow-sm border-0"),
        ], md=9),
    ], className="g-3"),
])


@callback(
    Output("s-table", "children"),
    Output("s-count", "children"),
    Output("s-chart", "figure"),
    Input("s-btn",   "n_clicks"),
    Input("s-query", "n_submit"),
    Input("s-genre", "value"),
    Input("s-price", "value"),
    Input("s-dur",   "value"),
    State("s-query", "value"),
)
def cb_search(n, ns, genre, price, max_dur, query):
    dff = df.copy()
    if query:
        q = query.lower()
        dff = dff[dff["artist_name"].str.lower().str.contains(q, na=False) |
                  dff["track_name"].str.lower().str.contains(q, na=False)]
    if genre and genre != "ALL":
        dff = dff[dff["genre"] == genre]
    dff = dff[(dff["track_price"] >= price[0]) & (dff["track_price"] <= price[1]) &
              (dff["duration_min"] <= max_dur)]

    badge = f"{len(dff):,} tracks"

    if dff.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(height=200)
        return dbc.Alert("No tracks match the current filters.", color="warning"), badge, empty_fig

    disp = dff[["track_name", "artist_name", "genre",
                "track_price", "duration_min", "release_year"]].head(50).copy()
    disp["track_price"]  = disp["track_price"].map("${:.2f}".format)
    disp["duration_min"] = disp["duration_min"].map("{:.2f} min".format)
    disp.columns = ["Track", "Artist", "Genre", "Price", "Duration", "Year"]
    table = html.Div([
        dbc.Table.from_dataframe(disp, striped=True, bordered=False, hover=True, size="sm"),
        html.Small(f"Showing top 50 of {len(dff):,} results", className="text-muted"),
    ], style={"maxHeight": "400px", "overflowY": "auto"})

    gc = dff["genre"].value_counts().head(10).reset_index()
    gc.columns = ["genre", "count"]
    fig = px.bar(gc, x="genre", y="count", color="count",
                 color_continuous_scale="Teal",
                 labels={"genre": "Genre", "count": "Tracks"})
    fig.update_layout(height=280, plot_bgcolor="white", showlegend=False,
                      coloraxis_showscale=False,
                      xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=True, gridcolor="#eee"),
                      margin=dict(t=10, b=20))
    return table, badge, fig


@callback(
    Output("s-query", "value"),
    Output("s-genre", "value"),
    Output("s-price", "value"),
    Output("s-dur",   "value"),
    Input("s-reset",  "n_clicks"),
    prevent_initial_call=True,
)
def cb_reset(_):
    return "", "ALL", [0.69, 1.29], 10
