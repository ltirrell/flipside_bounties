import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import ttest_ind

__all__ = [
    "n_players",
    "load_allday_data",
    "load_stats_data",
    "convert_df",
    "get_subset",
    "alt_mean_price",
    "get_metrics",
]

n_players = 40


@st.cache(ttl=3600 * 24)
def load_allday_data():
    df = pd.read_csv("data/current_allday_data.csv.gz")
    datecols = ["Datetime", "Date"]
    df[datecols] = df[datecols].apply(pd.to_datetime)
    return df


@st.cache(ttl=3600 * 24)
def load_stats_data(years=None):
    weekly_df = pd.read_csv("data/weekly_data.csv")
    season_df = pd.read_csv("data/season_data.csv")
    roster_df = pd.read_csv("data/roster_data.csv")
    team_df = pd.read_csv("data/team_desc.csv")
    season_df = season_df.merge(
        roster_df[
            ["player_id", "player_name", "position", "team", "headshot_url", "season"]
        ],
        on=["player_id", "season"],
    ).rename(columns={"player_name": "player_display_name"})

    weekly_df["team"] = weekly_df["recent_team"]

    if years is None:
        return weekly_df, season_df, roster_df, team_df
    elif type(years) == int:
        return (
            weekly_df[weekly_df.season == years],
            season_df[season_df.season == years],
            roster_df[roster_df.season == years],
            team_df,
        )
    else:
        return (
            weekly_df[weekly_df.season.isin(years)],
            season_df[season_df.season.isin(years)],
            roster_df[roster_df.season.isin(years)],
            team_df,
        )


@st.cache(ttl=3600 * 24)
def convert_df(df):
    """From: https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-pandas-dataframe-csv"""
    return df.to_csv().encode("utf-8")


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


def get_metrics(
    df,
    cols,
    metric,
    positions,
    short_form,
    pos_column="Position",
    agg_column="Price",
    summary=False,
):
    ntests = 1000  # approximate, for play types * positions * metrics * dates
    alpha = 0.05 / ntests  # Bonferroni correction for number tests
    for i, x in enumerate(positions):
        if x == "All":
            pos_data = df
        else:
            pos_data = df[df[pos_column] == x]

        if type(metric) == str:
            pos_metric = pos_data[pos_data[metric] == True]
            pos_no_metric = pos_data[pos_data[metric] == False]
        else:
            pos_metric = pos_data[pos_data[metric[0]] == True]
            pos_no_metric = pos_data[pos_data[metric[1]] == False]

        if summary:
            cols.metric(
                f"{short_form} Percentage: {x}", f"{len(pos_metric)/len(pos_data):.2%}"
            )
        else:
            pos_metric_agg = pos_metric[agg_column].values
            pos_no_metric_agg = pos_no_metric[agg_column].values

            pval = ttest_ind(pos_metric_agg, pos_no_metric_agg, equal_var=False).pvalue
            metric_mean = pos_metric_agg.mean()
            no_metric_mean = pos_no_metric_agg.mean()

            comp = (
                f"${metric_mean:,.2f} vs ${no_metric_mean:,.2f}"
                if agg_column == "Price"
                else f"{metric_mean:,.2f} vs {no_metric_mean:,.2f}"
            )

            if pd.isna(pval):
                sig = ""
                if pd.isna(metric_mean) and pd.isna(no_metric_mean):
                    comp = ""
                elif pd.isna(metric_mean):
                    comp = (
                        f"No {short_form}: ${no_metric_mean:,.2f}"
                        if agg_column == "Price"
                        else f"No {short_form}: {no_metric_mean:,.2f}"
                    )
                elif pd.isna(no_metric_mean):
                    comp = (
                        f"{short_form}: ${metric_mean:,.2f}"
                        if agg_column == "Price"
                        else f"{short_form}: {metric_mean:,.2f}"
                    )
            elif pval < alpha:
                if metric_mean > no_metric_mean:
                    sig = f"+ {short_form} HIGHER 📈"
                else:
                    sig = f"- {short_form} LOWER 📉"
            else:
                # sig = "- No Significant Difference"
                sig = ""

            if type(metric) != str:
                if len(pos_no_metric) == 0:
                    percentage = f"(No {short_form})"
                else:
                    percentage = f"({len(pos_metric)/len(pos_no_metric):,.2f} BG: Desc)"
            else:
                if len(pos_data) == 0:
                    percentage = f"(No {short_form})"
                else:
                    percentage = f"({len(pos_metric)/len(pos_data):.2%} {short_form})"

            cols[i % len(cols)].metric(
                f"Position: {x} {percentage}",
                comp,
                sig,
            )
