import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc
import pandas as pd
import numpy as np
import plotly.express as px

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "iTunes Music Dashboard"

# ── Load data globally so all pages can import it ─────────────────────────────
def load_data():
    df = pd.read_csv("Data/itunes_music_dataset.csv")
    df = df.dropna(subset=["artist_name", "release_date"])
    df["album_artist"] = df["album_artist"].fillna(df["artist_name"])
    df["track_price"] = df["track_price"].fillna(df["track_price"].median())
    df["collection_price"] = df["collection_price"].fillna(df["collection_price"].median())
    median_price = df[df["track_price"] > 0]["track_price"].median()
    df.loc[df["track_price"] < 0, "track_price"] = median_price
    df = df.drop(df["track_time_millis"].idxmax()).reset_index(drop=True)
    df["duration_min"] = df["track_time_millis"] / 60_000
    df["release_year"] = pd.to_datetime(df["release_date"]).dt.year
    df["price_tier"] = pd.cut(
        df["track_price"],
        bins=[-0.01, 0.70, 1.00, 1.30],
        labels=["Budget ($0.69)", "Standard ($0.99)", "Premium ($1.29)"],
    )
    df["genre_group"] = df["genre"].apply(
        lambda g: "Bollywood / Indian"
        if g in ["Bollywood", "Indian Pop", "Punjabi Pop", "Telugu"]
        else (
            "Western"
            if g in ["Pop", "Rock", "Hip-Hop/Rap", "R&B/Soul",
                     "Country", "Alternative", "Dance", "Electronic"]
            else "Other"
        )
    )
    return df

df = load_data()

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
