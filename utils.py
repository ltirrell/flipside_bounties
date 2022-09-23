import altair as alt
import pandas as pd
import streamlit as st

__all__ = [
    "n_players",
    "load_allday_data",
    "load_stats_data",
    "convert_df",
    "get_subset",
    "alt_mean_price",
]

n_players = 40


@st.cache(ttl=3600 * 24)
def load_allday_data():
    df = pd.read_csv("data/current_allday_data.csv.gz")
    datecols = ["Datetime", "Date"]
    df[datecols] = df[datecols].apply(pd.to_datetime)
    return df


@st.cache(ttl=3600 * 24)
def load_stats_data():
    weekly_df = pd.read_csv("data/weekly_data.csv")
    season_df = pd.read_csv("data/season_data.csv")
    roster_df = pd.read_csv("data/roster_data.csv")
    team_df = pd.read_csv("data/team_desc.csv")
    season_df = season_df.merge(
        roster_df[
            [
                "player_id",
                "player_name",
                "position",
                "team",
                "headshot_url",
            ]
        ],
        on="player_id",
    ).rename(columns={"player_name": "player_display_name"})

    weekly_df["team"] = weekly_df["recent_team"]

    return weekly_df, season_df, roster_df, team_df

@st.cache(ttl=3600 * 24)
def convert_df(df):
   """From: https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-pandas-dataframe-csv"""
   return df.to_csv().encode('utf-8')


def get_subset(df, col, val, n=n_players):
    return (
        df[df[col] == val]
        .sort_values("mean", ascending=False)
        .reset_index(drop=True)
        .iloc[:n]
    )


def alt_mean_price(
    df, col, color_col="Position", y_title="Mean Price ($)", y_labels=True
):
    chart = (
        (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X(col, title=col.replace("_", " "), sort="-y"),
                y=alt.Y("mean", title=y_title, axis=alt.Axis(labels=y_labels)),
                tooltip=[
                    alt.Tooltip(col, title=col.replace("_", " ")),
                    alt.Tooltip(f"{color_col}:N", title=color_col.replace("_", " ")),
                    alt.Tooltip("mean", title="Mean Price ($)", format=".2f"),
                    alt.Tooltip("count", title="Total Sales", format=","),
                ],
                color=alt.Color(
                    f"{color_col}:N",
                    sort=alt.EncodingSortField(color_col, op="max", order="ascending"),
                    scale=alt.Scale(
                        scheme="paired",
                    ),
                ),
            )
        )
        .interactive()
        .properties(height=600)
    )
    return chart
