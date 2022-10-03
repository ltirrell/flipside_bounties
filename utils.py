import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import ttest_ind
import json

__all__ = [
    "n_players",
    "load_allday_data",
    "load_stats_data",
    "convert_df",
    "get_subset",
    "alt_mean_price",
    "get_metrics",
    "get_position_group",
    "cols_to_keep",
    "score_columns",
    "td_mapping",
    "all_pos",
    "offense",
    "defense",
    "team_pos",
    "pos_groups",
    "positions",
    "rarities",
    "position_type_dict",
    "agg_dict",
    "main_date_ranges",
    "play_v_player_date_ranges",
    "get_ttests",
    "stats_date_ranges",
    "load_score_data",
    "load_ttest",
    "stats_subset",
    "load_player_data",
    "load_play_v_player_data"
]

cols_to_keep = [
    "Date",
    "Datetime",
    "marketplace_id",
    "Player",
    "Team",
    "Position",
    # "Position Group",
    "Play_Type",
    "Season",
    "Week",
    "Moment_Date",
    "Game Outcome",
    "won_game",
    # "Scored Touchdown?",
    "Moment_Tier",
    "Rarity",
    "Moment_Description",
    "NFLALLDAY_ASSETS_URL",
    "Total_Circulation",
    "Price",
    "tx_id",
    "scored_td_in_moment",
    "pbp_td",
    "description_td",
    "scored_td_in_game",
    "game_td",
]

score_columns = [
    "Pass",
    "Reception",
    "Rush",
    "Strip Sack",
    "Interception",
    "Fumble Recovery",  # ~50% TD
    "Blocked Kick",  # 1/4 not td
    "Punt Return",  # all TD
    "Kick Return",  # 1/6 not td
]

td_mapping = {
    "scored_td_in_moment": "Best Guess (Moment TD)",
    "pbp_td": "Conservative (Moment TD)",
    "description_td": "Description only (Moment TD)",
    "scored_td_in_game": "Best Guess: (In-game TD)",
    "game_td": "Conservative (In-game TD)",
}


all_pos = ["All"]
offense = [
    "QB",
    "WR",
    "RB",
    "TE",
    "OL",
]
defense = [
    "DB",
    "DL",
    "LB",
]
team_pos = ["Team"]
pos_groups = ["All", "Offense", "Defense", "Team"]
positions = all_pos + offense + defense + team_pos
rarities = ["COMMON", "RARE", "LEGENDARY", "ULTIMATE"]

main_date_ranges = [
    "All Time",
    "2022 Full Season",
    "2022 Week 1",
    "2022 Week 2",
    "2022 Week 3",
]
play_v_player_date_ranges =         [
            "All dates",
            "Since 2022 preseason",
            "Since 2022 Week 1",
            "Since 2022 Week 2",
            "Since 2022 Week 3",
        ]
stats_date_ranges = ["2022 Full Season", "2022 Week 1", "2022 Week 2", "2022 Week 3"]

position_type_dict = {
    "By Position": ("Position", positions),
    "By Group": ("Position Group", pos_groups),
    "By Rarity": ("Moment_Tier", rarities),
}

agg_dict = {
    "Player": "first",
    "Team": "first",
    "Position": "first",
    "Position Group": "first",
    "Play_Type": "first",
    "Season": "first",
    "Week": "first",
    "Moment_Date": "first",
    "Game Outcome": "first",
    "won_game": "first",
    # "Scored Touchdown?": "first",
    "Description only (Moment TD)": "first",
    "Conservative (In-game TD)": "first",
    "Conservative (Moment TD)": "first",
    "Best Guess: (In-game TD)": "first",
    "Best Guess (Moment TD)": "first",
    "Moment_Tier": "first",
    "Rarity": "first",
    "Moment_Description": "first",
    "NFLALLDAY_ASSETS_URL": "first",
    "Total_Circulation": "first",
    "Price": "mean",
    "tx_id": "count",
}

stats_subset = [
    "player_id",
    "player_display_name",
    "position",
    "team",
    "headshot_url",
    "season",
    # "week",
    "fantasy_points_ppr",
    "passing_tds",
    "passing_yards",
    "receiving_tds",
    "receiving_yards",
    "rushing_tds",
    "rushing_yards",
]

n_players = 40


@st.cache(ttl=3600 * 24, allow_output_mutation=True)
def load_allday_data(cols=None):
    if cols is not None:
        df = pd.read_csv("data/current_allday_data.csv.gz", usecols=cols)
    else:
        df = pd.read_csv("data/current_allday_data.csv.gz")
    datecols = ["Datetime", "Date"]
    df[datecols] = df[datecols].apply(pd.to_datetime)
    return df


@st.cache(ttl=3600 * 24, allow_output_mutation=True)
def load_stats_data(years=None, subset=False):
    # NOTE: now returning less data

    weekly_df = pd.read_csv("data/weekly_data.csv")
    season_df = pd.read_csv("data/season_data.csv")
    roster_df = pd.read_csv("data/roster_data.csv")
    # team_df = pd.read_csv("data/team_desc.csv")
    season_df = season_df.merge(
        roster_df[
            ["player_id", "player_name", "position", "team", "headshot_url", "season"]
        ],
        on=["player_id", "season"],
    ).rename(columns={"player_name": "player_display_name"})
    if subset:
        season_df = season_df[stats_subset]

    weekly_df["team"] = weekly_df["recent_team"]
    if subset:
        weekly_df = weekly_df[
            [
                "player_id",
                "player_display_name",
                "position",
                "team",
                "headshot_url",
                "season",
                "week",
                "fantasy_points_ppr",
                "passing_tds",
                "passing_yards",
                "receiving_tds",
                "receiving_yards",
                "rushing_tds",
                "rushing_yards",
            ]
        ]

    if years is None:
        return weekly_df, season_df  # , roster_df, team_df
    elif type(years) == int:
        return (
            weekly_df[weekly_df.season == years],
            season_df[season_df.season == years],
            # roster_df[roster_df.season == years],
            # team_df,
        )
    else:
        return (
            weekly_df[weekly_df.season.isin(years)],
            season_df[season_df.season.isin(years)],
            # roster_df[roster_df.season.isin(years)],
            # team_df,
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


def get_position_group(x):
    if x in offense:
        return "Offense"
    if x in defense:
        return "Defense"
    if x in team_pos:
        return "Team"


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


def get_ttests(
    df,
    metric,
    positions,
    short_form,
    pos_column="Position",
    agg_column="Price",
):
    ntests = 1000  # approximate, for play types * positions * metrics * dates
    alpha = 0.05 / ntests  # Bonferroni correction for number tests
    vals = []
    for x in positions:
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

        label = f"Position: {x} {percentage}"
        vals.append((label, comp, sig))

    return vals


@st.cache(ttl=3600 * 24)
def load_score_data(date_range, how_scores, play_type):
    date_str = date_range.replace(" ", "_")
    df = pd.read_csv(f"data/cache/{date_str}--grouped.csv")
    df["Scored Touchdown?"] = df[how_scores]
    if play_type != "All":
        df = df[df.Play_Type == play_type]
    return df


# @st.cache(ttl=3600 * 24)
def load_ttest(
    date_range,
    play_type,
    how_scores,
    agg_metric,
    position_type,
    metric,
    short_form,
):
    with open("data/cache/score_ttest_results.json") as f:
        data = json.load(f)
    key = (
        f"{date_range}--{play_type}--{how_scores}--{agg_metric}--{position_type}--{metric}--{short_form}".replace(
            " ", "_"
        )
        .replace(")", "")
        .replace("(", "")
    )
    return data[key]

# @st.cache(ttl=3600 * 24)
def load_player_data(date_range, agg_metric):
    date_str = date_range.replace(" ", "_")
    df = pd.read_csv(f"data/cache/player-{date_str}-{agg_metric}--grouped.csv")
    return df

@st.cache(ttl=3600 * 24)
def load_play_v_player_data(date_range):
    date_str = date_range.replace(" ", "_")
    play_type_price_data = pd.read_csv(f"data/cache/play_v_player-play_type-{date_str}--grouped.csv")
    play_type_tier_price_data = pd.read_csv(f"data/cache/play_v_player-play_type_tier-{date_str}--grouped.csv")
    player_tier_price_data = pd.read_csv(f"data/cache/play_v_player-player_tier-{date_str}--grouped.csv")
    topN_player_data = pd.read_csv(f"data/cache/play_v_player-topN_player-{date_str}--grouped.csv")
    return (
            play_type_price_data,
            play_type_tier_price_data,
            player_tier_price_data,
            topN_player_data,
        )