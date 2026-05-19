import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from data import df

dash.register_page(__name__, path="/genres", name="Genre Explorer")

SAFE       = px.colors.qualitative.Safe
ALL_GENRES = sorted(df["genre"].unique())
TOP8       = df["genre"].value_counts().head(8).index.tolist()

layout = html.Div([
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.B("Controls")),
            dbc.CardBody([
                html.Label("Select Genres", className="fw-semibold small mb-1"),

                dbc.ButtonGroup([
                    dbc.Button("Select All", id="g-select-all", size="sm",
                               color="primary", outline=True, n_clicks=0),
                    dbc.Button("Clear All",  id="g-clear-all",  size="sm",
                               color="secondary", outline=True, n_clicks=0),
                ], className="mb-2 w-100"),
                dcc.Dropdown(id="g-genres",
                             options=[{"label": g, "value": g} for g in ALL_GENRES],
                             value=TOP8, multi=True, className="mb-3"),
                html.Label("Min Track Count", className="fw-semibold small mb-1"),
                dcc.Slider(id="g-min", min=10, max=500, step=10, value=50,
                           marks={10: "10", 100: "100", 300: "300", 500: "500"},
                           tooltip={"placement": "bottom", "always_visible": True},
                           className="mb-3"),
                html.Label("Bubble metric", className="fw-semibold small mb-1"),
                dbc.RadioItems(id="g-metric",
                               options=[
                                   {"label": "Total Revenue", "value": "total_revenue"},
                                   {"label": "Avg Duration",  "value": "avg_duration"},
                                   {"label": "Track Count",   "value": "num_tracks"},
                               ],
                               value="total_revenue"),
            ]),
        ], className="shadow-sm border-0", style={"position": "sticky", "top": "70px"}), md=3),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.B("Genre Revenue Landscape")),
                dbc.CardBody(dcc.Graph(id="g-bubble", config={"displayModeBar": False})),
            ], className="shadow-sm border-0 mb-3"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader(html.B("Duration Distribution (Box)")),
                    dbc.CardBody(dcc.Graph(id="g-box", config={"displayModeBar": False})),
                ], className="shadow-sm border-0"), md=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader(html.B("Genre Summary Table")),
                    dbc.CardBody(html.Div(id="g-table",
                                          style={"maxHeight": "340px", "overflowY": "auto"})),
                ], className="shadow-sm border-0"), md=6),
            ], className="g-3"),
        ], md=9),
    ], className="g-3"),
])


@callback(
    Output("g-genres", "value"),
    Input("g-select-all", "n_clicks"),
    Input("g-clear-all",  "n_clicks"),
    State("g-genres", "value"),
    prevent_initial_call=True,
)
def cb_select_all(select_clicks, clear_clicks, current):
    from dash import ctx
    if ctx.triggered_id == "g-select-all":
        return ALL_GENRES
    elif ctx.triggered_id == "g-clear-all":
        return []
    return current


@callback(
    Output("g-bubble", "figure"),
    Output("g-box",    "figure"),
    Output("g-table",  "children"),
    Input("g-genres",  "value"),
    Input("g-min",     "value"),
    Input("g-metric",  "value"),
)
def cb_genres(genres, min_tracks, metric):
    genres = genres or TOP8
    dff = df[df["genre"].isin(genres)]
    gr = dff.groupby("genre").agg(
        num_tracks    =("track_id",    "count"),
        avg_price     =("track_price", "mean"),
        total_revenue =("track_price", "sum"),
        avg_duration  =("duration_min","mean"),
    ).reset_index()
    gr = gr[gr["num_tracks"] >= min_tracks]

    bubble = px.scatter(
        gr, x="num_tracks", y="avg_price", size=metric, color=metric,
        color_continuous_scale="Viridis", text="genre",
        hover_data={"total_revenue": ":$.2f", "avg_duration": ":.2f"},
        labels={"num_tracks": "Tracks", "avg_price": "Avg Price ($)"},
    )
    bubble.update_traces(textposition="top center", textfont_size=10)
    bubble.update_layout(height=380, plot_bgcolor="white",
                         xaxis=dict(showgrid=True, gridcolor="#eee"),
                         yaxis=dict(showgrid=True, gridcolor="#eee", range=[1.05, 1.35]),
                         margin=dict(t=10, b=10))

    order = dff.groupby("genre")["duration_min"].median().sort_values().index.tolist()
    box = go.Figure()
    for i, g in enumerate(order):
        box.add_trace(go.Box(
            y=dff[dff["genre"] == g]["duration_min"], name=g, boxmean=True,
            marker_color=SAFE[i % len(SAFE)],
            line=dict(color="#333", width=1.5),
            fillcolor=SAFE[i % len(SAFE)], opacity=0.7,
        ))
    box.update_layout(height=320, plot_bgcolor="white", showlegend=False,
                      yaxis=dict(showgrid=True, gridcolor="#eee",
                                 title="Duration (min)", range=[0, 12]),
                      margin=dict(t=10, b=10))

    if gr.empty:
        table = dbc.Alert("No genres match filters.", color="warning")
    else:
        t = gr.sort_values("total_revenue", ascending=False).reset_index(drop=True).copy()
        t["avg_price"]     = t["avg_price"].map("${:.2f}".format)
        t["total_revenue"] = t["total_revenue"].map("${:,.0f}".format)
        t["avg_duration"]  = t["avg_duration"].map("{:.2f} min".format)
        t.columns = ["Genre", "Tracks", "Avg Price", "Revenue", "Avg Duration"]
        table = dbc.Table.from_dataframe(t, striped=True, bordered=False, hover=True, size="sm")

    return bubble, box, table