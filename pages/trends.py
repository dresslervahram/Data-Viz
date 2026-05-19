import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from data import df

dash.register_page(__name__, path="/trends", name="Release Trends")

SAFE     = px.colors.qualitative.Safe
TOP8     = df["genre"].value_counts().head(8).index.tolist()
YEAR_MIN = int(df["release_year"].min())
YEAR_MAX = int(df["release_year"].max())
CLR      = {"blue": "#3d85c8", "orange": "#f6a623", "red": "#e74c3c", "green": "#a8d8a8"}

layout = html.Div([
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.B("Controls")),
            dbc.CardBody([
                html.Label("Year Range", className="fw-semibold small mb-1"),
                dcc.RangeSlider(id="t-years", min=YEAR_MIN, max=YEAR_MAX, step=1,
                                value=[2005, YEAR_MAX],
                                marks={y: str(y) for y in range(YEAR_MIN, YEAR_MAX+1, 5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-3"),
                html.Label("Group by", className="fw-semibold small mb-1"),
                dbc.RadioItems(id="t-group",
                               options=[{"label": "Genre Group", "value": "genre_group"},
                                        {"label": "Price Tier",  "value": "price_tier"}],
                               value="genre_group", inline=True, className="mb-3"),
                html.Label("Chart type", className="fw-semibold small mb-1"),
                dbc.RadioItems(id="t-type",
                               options=[{"label": "Area", "value": "area"},
                                        {"label": "Line", "value": "line"},
                                        {"label": "Bar",  "value": "bar"}],
                               value="area", inline=True),
            ]),
        ], className="shadow-sm border-0", style={"position": "sticky", "top": "70px"}), md=3),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.B("Tracks Released Per Year")),
                dbc.CardBody(dcc.Graph(id="t-main", config={"displayModeBar": False})),
            ], className="shadow-sm border-0 mb-3"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader(html.B("Top Artists (period)")),
                    dbc.CardBody(dcc.Graph(id="t-artists", config={"displayModeBar": False})),
                ], className="shadow-sm border-0"), md=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader(html.B("Duration × Price")),
                    dbc.CardBody(dcc.Graph(id="t-scatter", config={"displayModeBar": False})),
                ], className="shadow-sm border-0"), md=6),
            ], className="g-3"),
        ], md=9),
    ], className="g-3"),
])


@callback(
    Output("t-main",    "figure"),
    Output("t-artists", "figure"),
    Output("t-scatter", "figure"),
    Input("t-years", "value"),
    Input("t-group", "value"),
    Input("t-type",  "value"),
)
def cb_trends(years, groupby, chart_type):
    y0, y1 = years
    dff = df[(df["release_year"] >= y0) & (df["release_year"] <= y1)].copy()
    dff["price_tier"] = dff["price_tier"].astype(str)

    yg = dff.groupby(["release_year", groupby]).size().reset_index(name="tracks")
    cmap = {
        "Western": CLR["blue"], "Bollywood / Indian": CLR["orange"], "Other": CLR["green"],
        "Budget ($0.69)": CLR["blue"], "Standard ($0.99)": CLR["orange"],
        "Premium ($1.29)": CLR["red"],
    }
    kw = dict(data_frame=yg, x="release_year", y="tracks", color=groupby,
              color_discrete_map=cmap,
              labels={"release_year": "Year", "tracks": "Tracks",
                      groupby: groupby.replace("_", " ").title()})

    main = (px.area(**kw) if chart_type == "area"
            else px.line(**kw, markers=True) if chart_type == "line"
            else px.bar(**kw, barmode="stack"))
    main.update_layout(height=380, plot_bgcolor="white",
                       xaxis=dict(showgrid=False, dtick=2),
                       yaxis=dict(showgrid=True, gridcolor="#eee"),
                       legend=dict(orientation="h", y=-0.2),
                       margin=dict(t=10, b=70))

    ta = dff["artist_name"].value_counts().head(10).reset_index()
    ta.columns = ["artist", "count"]
    ta = ta.sort_values("count")
    artists = px.bar(ta, x="count", y="artist", orientation="h",
                     color="count", color_continuous_scale="Blues",
                     labels={"count": "Tracks", "artist": ""})
    artists.update_layout(height=320, plot_bgcolor="white", showlegend=False,
                          coloraxis_showscale=False,
                          xaxis=dict(showgrid=True, gridcolor="#eee"),
                          margin=dict(t=10, b=10, l=5, r=10))

    ds = dff[dff["genre"].isin(TOP8) & (dff["duration_min"] <= 10)]
    sc = px.scatter(ds, x="duration_min", y="track_price", color="genre",
                    opacity=0.4, color_discrete_sequence=SAFE,
                    labels={"duration_min": "Duration (min)", "track_price": "Price ($)"})
    for price, lbl, c in [(0.69, "$0.69", CLR["blue"]),
                          (0.99, "$0.99", CLR["orange"]),
                          (1.29, "$1.29", CLR["red"])]:
        sc.add_hline(y=price, line_dash="dot", line_color=c,
                     annotation_text=lbl, annotation_position="right")
    sc.update_layout(height=320, plot_bgcolor="white",
                     xaxis=dict(showgrid=True, gridcolor="#eee"),
                     yaxis=dict(showgrid=False, tickvals=[0.69, 0.99, 1.29]),
                     legend=dict(orientation="h", y=-0.4, font_size=9),
                     margin=dict(t=10, b=90))

    return main, artists, sc
