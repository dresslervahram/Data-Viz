import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from data import df

dash.register_page(__name__, path="/", name="Overview")

CLR = {"blue": "#3d85c8", "orange": "#f6a623", "red": "#e74c3c", "green": "#a8d8a8"}


def kpi(title, value, icon, color):
    return dbc.Card(dbc.CardBody(
        html.Div([
            html.I(className=f"bi {icon} fs-2 me-3", style={"color": color}),
            html.Div([
                html.P(title, className="text-muted mb-0",
                       style={"fontSize": "0.78rem", "textTransform": "uppercase",
                              "letterSpacing": "0.05em"}),
                html.H4(value, className="mb-0 fw-bold"),
            ]),
        ], className="d-flex align-items-center")
    ), className="shadow-sm border-0 h-100")


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

layout = html.Div([
    dbc.Row([
        dbc.Col(kpi("Total Tracks", f"{len(df):,}",
                    "bi-collection-fill", CLR["blue"]), md=3),
        dbc.Col(kpi("Genres", str(df["genre"].nunique()),
                    "bi-vinyl-fill", CLR["orange"]), md=3),
        dbc.Col(kpi("Artists", f"{df['artist_name'].nunique():,}",
                    "bi-person-fill", CLR["blue"]), md=3),
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
                    "78.9% of tracks are priced at the Premium tier ($1.29)."]),
                dbc.ListGroupItem([html.I(className="bi bi-3-circle-fill text-primary me-2"),
                    "Catalog releases peaked in 2016–2017, declining since."]),
                dbc.ListGroupItem([html.I(className="bi bi-4-circle-fill text-danger me-2"),
                    "Track duration does NOT correlate with price across any genre."]),
            ], flush=True)),
        ], className="shadow-sm border-0 h-100"), md=6),
    ], className="g-3"),
])
