import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "iTunes Music Dashboard"

# ── Data ───────────────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv('/Users/vahramdressler/Desktop/YSU/S2/Data_Viz/Data-Viz/Data/itunes_music_dataset.csv')
    df = df.dropna(subset=["artist_name", "release_date"])
    df["album_artist"] = df["album_artist"].fillna(df["artist_name"])
    df["track_price"] = df["track_price"].fillna(df["track_price"].median())
    df["collection_price"] = df["collection_price"].fillna(df["collection_price"].median())
    median_price = df[df["track_price"] > 0]["track_price"].median()
    df.loc[df["track_price"] < 0, "track_price"] = median_price
    df = df.drop(df["track_time_millis"].idxmax()).reset_index(drop=True)
    df["duration_min"]  = df["track_time_millis"] / 60_000
    df["release_year"]  = pd.to_datetime(df["release_date"]).dt.year
    df["price_tier"]    = pd.cut(
        df["track_price"],
        bins=[-0.01, 0.70, 1.00, 1.30],
        labels=["Budget ($0.69)", "Standard ($0.99)", "Premium ($1.29)"],
    )
    df["genre_group"] = df["genre"].apply(
        lambda g: "Bollywood / Indian"
        if g in ["Bollywood", "Indian Pop", "Punjabi Pop", "Telugu"]
        else ("Western" if g in ["Pop", "Rock", "Hip-Hop/Rap", "R&B/Soul",
                                  "Country", "Alternative", "Dance", "Electronic"]
              else "Other")
    )
    return df

df = load_data()
ALL_GENRES  = sorted(df["genre"].unique())
TOP8        = df["genre"].value_counts().head(8).index.tolist()
YEAR_MIN    = int(df["release_year"].min())
YEAR_MAX    = int(df["release_year"].max())
SAFE        = px.colors.qualitative.Safe
CLR         = {"blue": "#3d85c8", "orange": "#f6a623", "red": "#e74c3c", "green": "#a8d8a8"}


# ── Helpers ────────────────────────────────────────────────────────────────────
def kpi(title, value, icon, color):
    return dbc.Card(dbc.CardBody(
        html.Div([
            html.I(className=f"bi {icon} fs-2 me-3", style={"color": color}),
            html.Div([
                html.P(title, className="text-muted mb-0",
                       style={"fontSize": "0.78rem", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.H4(value, className="mb-0 fw-bold"),
            ]),
        ], className="d-flex align-items-center")
    ), className="shadow-sm border-0 h-100")


# ── Navbar ─────────────────────────────────────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand([html.I(className="bi bi-music-note-beamed me-2"), "iTunes Music Dashboard"],
                        href="/", className="fw-bold fs-5"),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Overview",       href="/")),
            dbc.NavItem(dbc.NavLink("Genre Explorer", href="/genres")),
            dbc.NavItem(dbc.NavLink("Release Trends", href="/trends")),
            dbc.NavItem(dbc.NavLink("Track Search",   href="/search")),
        ], navbar=True, className="ms-auto"),
    ], fluid=True),
    color="primary", dark=True, sticky="top", className="mb-0 shadow",
)

# ── Root layout ────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    navbar,
    dbc.Container(html.Div(id="page-content"), fluid=True, className="py-4"),
])


# ── Pages ──────────────────────────────────────────────────────────────────────
def page_overview():
    # Treemap
    gc = df["genre"].value_counts().head(15).reset_index()
    gc.columns = ["genre", "count"]
    gc["pct"] = (gc["count"] / gc["count"].sum() * 100).round(1)
    treemap = px.treemap(gc, path=["genre"], values="count", color="count",
                         color_continuous_scale="Teal", custom_data=["pct"])
    treemap.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,}<br>%{customdata[0]:.1f}%",
        textfont_size=12)
    treemap.update_layout(height=400, coloraxis_showscale=False,
                          margin=dict(t=5, l=5, r=5, b=5))

    # Price bar
    tc = df["price_tier"].value_counts().reset_index()
    tc.columns = ["tier", "count"]
    tc["pct"] = (tc["count"] / tc["count"].sum() * 100).round(1)
    tc = tc.sort_values("tier")
    pricebar = go.Figure(go.Bar(
        x=tc["tier"], y=tc["count"],
        text=[f"{p:.1f}%" for p in tc["pct"]], textposition="outside",
        marker_color=[CLR["blue"], CLR["orange"], CLR["red"]],
        hovertemplate="<b>%{x}</b><br>%{y:,} tracks<extra></extra>",
    ))
    pricebar.update_layout(plot_bgcolor="white", height=320,
                           yaxis=dict(showgrid=True, gridcolor="#eee"),
                           margin=dict(t=10, b=10, l=10, r=10))

    # Top artists
    ta = df["artist_name"].value_counts().head(10).reset_index()
    ta.columns = ["artist", "count"]
    ta = ta.sort_values("count")
    artists = px.bar(ta, x="count", y="artist", orientation="h",
                     color="count", color_continuous_scale="Blues",
                     labels={"count": "Tracks", "artist": ""})
    artists.update_layout(height=340, plot_bgcolor="white", showlegend=False,
                          coloraxis_showscale=False,
                          xaxis=dict(showgrid=True, gridcolor="#eee"),
                          margin=dict(t=10, b=10, l=5, r=10))

    return html.Div([
        dbc.Row([
            dbc.Col(kpi("Total Tracks",  f"{len(df):,}",
                        "bi-collection-fill", CLR["blue"]),   md=3),
            dbc.Col(kpi("Genres",        str(df["genre"].nunique()),
                        "bi-vinyl-fill",       CLR["orange"]), md=3),
            dbc.Col(kpi("Artists",       f"{df['artist_name'].nunique():,}",
                        "bi-person-fill",      CLR["blue"]),   md=3),
            dbc.Col(kpi("Premium Priced",
                        f"{(df['price_tier']=='Premium ($1.29)').mean()*100:.1f}%",
                        "bi-tag-fill", CLR["red"]), md=3),
        ], className="g-3 mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.B("Top 15 Genres – Track Count")),
                dbc.CardBody(dcc.Graph(figure=treemap, config={"displayModeBar": False})),
            ], className="shadow-sm border-0"), md=7),
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.B("Price Tier Distribution")),
                dbc.CardBody(dcc.Graph(figure=pricebar, config={"displayModeBar": False})),
            ], className="shadow-sm border-0"), md=5),
        ], className="g-3 mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.B("Top 10 Artists by Track Count")),
                dbc.CardBody(dcc.Graph(figure=artists, config={"displayModeBar": False})),
            ], className="shadow-sm border-0"), md=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.B("Key Insights")),
                dbc.CardBody(dbc.ListGroup([
                    dbc.ListGroupItem([html.I(className="bi bi-1-circle-fill text-primary me-2"),
                        "Pop & Bollywood together account for ~46% of all tracks."]),
                    dbc.ListGroupItem([html.I(className="bi bi-2-circle-fill text-warning me-2"),
                        "78.9% of tracks are priced at the Premium tier ($1.29) — pricing is not a competitive lever."]),
                    dbc.ListGroupItem([html.I(className="bi bi-3-circle-fill text-primary me-2"),
                        "Catalog releases peaked in 2016–2017, declining since — streaming is winning."]),
                    dbc.ListGroupItem([html.I(className="bi bi-4-circle-fill text-danger me-2"),
                        "Track duration does NOT correlate with price across any genre."]),
                ], flush=True)),
            ], className="shadow-sm border-0 h-100"), md=6),
        ], className="g-3"),
    ])


def page_genres():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader(html.B("Controls")),
                dbc.CardBody([
                    html.Label("Select Genres", className="fw-semibold small mb-1"),
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
                                       {"label": "Total Revenue",  "value": "total_revenue"},
                                       {"label": "Avg Duration",   "value": "avg_duration"},
                                       {"label": "Track Count",    "value": "num_tracks"},
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


@app.callback(
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
        t["avg_price"]      = t["avg_price"].map("${:.2f}".format)
        t["total_revenue"]  = t["total_revenue"].map("${:,.0f}".format)
        t["avg_duration"]   = t["avg_duration"].map("{:.2f} min".format)
        t.columns = ["Genre", "Tracks", "Avg Price", "Revenue", "Avg Duration"]
        table = dbc.Table.from_dataframe(t, striped=True, bordered=False,
                                         hover=True, size="sm")
    return bubble, box, table


def page_trends():
    return html.Div([
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


@app.callback(
    Output("t-main",    "figure"),
    Output("t-artists", "figure"),
    Output("t-scatter", "figure"),
    Input("t-years",  "value"),
    Input("t-group",  "value"),
    Input("t-type",   "value"),
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

    main = (px.area(**kw)               if chart_type == "area"
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


def page_search():
    return html.Div([
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


@app.callback(
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


@app.callback(
    Output("s-query", "value"),
    Output("s-genre", "value"),
    Output("s-price", "value"),
    Output("s-dur",   "value"),
    Input("s-reset",  "n_clicks"),
    prevent_initial_call=True,
)
def cb_reset(_):
    return "", "ALL", [0.69, 1.29], 10


# ── Router ─────────────────────────────────────────────────────────────────────
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(pathname):
    if pathname in ("/", ""):  return page_overview()
    if pathname == "/genres":  return page_genres()
    if pathname == "/trends":  return page_trends()
    if pathname == "/search":  return page_search()
    return dbc.Alert("404 – Page not found.", color="danger")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)