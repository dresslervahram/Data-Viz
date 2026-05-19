import pandas as pd
import os

# Resolve the CSV path relative to this file so it works both locally and on Render
_BASE = os.path.dirname(os.path.abspath(__file__))
_CSV  = os.path.join(_BASE, "Data", "itunes_music_dataset.csv")

def load_data():
    df = pd.read_csv(_CSV)

    # ── Drop rows missing critical columns ────────────────────────────────────
    df = df.dropna(subset=["artist_name", "release_date"])

    # ── Fill missing values ───────────────────────────────────────────────────
    df["album_artist"]      = df["album_artist"].fillna(df["artist_name"])
    df["track_price"]       = df["track_price"].fillna(df["track_price"].median())
    df["collection_price"]  = df["collection_price"].fillna(df["collection_price"].median())

    # Fix negative prices
    median_price = df[df["track_price"] > 0]["track_price"].median()
    df.loc[df["track_price"] < 0, "track_price"] = median_price

    # ── Remove the outlier track with the longest duration ────────────────────
    df = df.drop(df["track_time_millis"].idxmax()).reset_index(drop=True)

    # ── Derived columns ───────────────────────────────────────────────────────
    df["duration_min"]  = df["track_time_millis"] / 60_000
    df["release_year"]  = pd.to_datetime(df["release_date"]).dt.year

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