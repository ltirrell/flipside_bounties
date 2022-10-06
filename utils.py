import json
from urllib.request import urlopen

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from scipy.stats import ttest_ind, ttest_rel

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
    "load_play_v_player_data",
    "load_headshot",
    "load_challenge_data",
    "player_mapping",
    "week_timings",
    "game_timings",
    "load_challenge_player_data",
    "alt_challenge_chart",
    "get_challenge_summary",
    "get_challenge_ttests",
    "alt_challenge_game",
    "load_challenge_reward",
]

cols_to_keep = [
    "Date",
    "Datetime",
    "marketplace_id",
    "Player",
    "Team",
    "Position",
    "Series",
    "Set_Name",
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

# #TODO: clean up date ranges
main_date_ranges = [
    "All Time",
    "2022 Full Season",
    "2022 Week 1",
    "2022 Week 2",
    "2022 Week 3",
    "2022 Week 4",
]
play_v_player_date_ranges = [
    "All dates",
    "Since 2022 preseason",
    "Since 2022 Week 1",
    "Since 2022 Week 2",
    "Since 2022 Week 3",
    "Since 2022 Week 4",
]
stats_date_ranges = [
    "2022 Full Season",
    "2022 Week 1",
    "2022 Week 2",
    "2022 Week 3",
    "2022 Week 4",
]

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
    "Series": "first",
    "Set_Name": "first",
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

player_mapping = {
    "Patrick Mahomes": "Patrick Mahomes II",
    "Gabe Davis	": "Gabriel Davis",
}

week_timings = {
    1: ("2022-09-08", "2022-09-15"),
    2: ("2022-09-15", "2022-09-22"),
    3: ("2022-09-22", "2022-09-29"),
    4: ("2022-09-29", "2022-10-06"),
}

game_timings = {
    1: {
        "thursday": (
            pd.Timestamp("2022-09-08 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-08 23:00:00-0400", tz="US/Eastern"),
        ),
        "slate": (
            pd.Timestamp("2022-09-11 13:00:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-11 19:30:00-0400", tz="US/Eastern"),
        ),
        "sunday_night": (
            pd.Timestamp("2022-09-11 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-11 23:00:00-0400", tz="US/Eastern"),
        ),
        "monday": (
            pd.Timestamp("2022-09-12 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-12 23:00:00-0400", tz="US/Eastern"),
        ),
        "weekly": (
            pd.Timestamp("2022-09-08 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-12 23:00:00-0400", tz="US/Eastern"),
        ),
    },
    2: {
        "thursday": (
            pd.Timestamp("2022-09-15 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-15 23:00:00-0400", tz="US/Eastern"),
        ),
        "slate": (
            pd.Timestamp("2022-09-18 13:00:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-18 19:30:00-0400", tz="US/Eastern"),
        ),
        "sunday_night": (
            pd.Timestamp("2022-09-18 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-18 23:00:00-0400", tz="US/Eastern"),
        ),
        "monday": (
            pd.Timestamp("2022-09-19 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-19 23:00:00-0400", tz="US/Eastern"),
        ),
        "weekly": (
            pd.Timestamp("2022-09-15 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-19 23:00:00-0400", tz="US/Eastern"),
        ),
    },
    3: {
        "thursday": (
            pd.Timestamp("2022-09-22 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-22 23:00:00-0400", tz="US/Eastern"),
        ),
        "slate": (
            pd.Timestamp("2022-09-25 09:30:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-25 19:30:00-0400", tz="US/Eastern"),
        ),
        "sunday_night": (
            pd.Timestamp("2022-09-25 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-25 23:00:00-0400", tz="US/Eastern"),
        ),
        "monday": (
            pd.Timestamp("2022-09-26 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-26 23:00:00-0400", tz="US/Eastern"),
        ),
        "weekly": (
            pd.Timestamp("2022-09-22 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-26 23:00:00-0400", tz="US/Eastern"),
        ),
    },
    4: {  # #TODO: add for
        "thursday": (
            pd.Timestamp("2022-09-29 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-09-29 23:00:00-0400", tz="US/Eastern"),
        ),
        "slate": (
            pd.Timestamp("2022-10-02 09:30:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-10-02 19:30:00-0400", tz="US/Eastern"),
        ),
        "sunday_night": (
            pd.Timestamp("2022-10-02 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-10-02 23:00:00-0400", tz="US/Eastern"),
        ),
        "monday": (
            pd.Timestamp("2022-10-03 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-10-03 23:00:00-0400", tz="US/Eastern"),
        ),
        "weekly": (
            pd.Timestamp("2022-09-29 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-10-03 23:00:00-0400", tz="US/Eastern"),
        ),
        "bills_ravens": (
            pd.Timestamp("2022-10-02 13:00:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-10-02 16:15:00-0400", tz="US/Eastern"),
        ),
        "49ers_rams": (
            pd.Timestamp("2022-10-03 20:15:00-0400", tz="US/Eastern"),
            pd.Timestamp("2022-10-03 23:00:00-0400", tz="US/Eastern"),
        ),
    },
}

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


@st.cache(ttl=3600 * 24 * 7)
def load_headshot(headshot_url):
    image = Image.open(urlopen(headshot_url))
    basewidth = 200
    wpercent = basewidth / float(image.size[0])
    hsize = int((float(image.size[1]) * float(wpercent)))
    image = image.resize((basewidth, hsize), Image.Resampling.LANCZOS)
    return image


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


@st.cache(ttl=3600 * 24)
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


@st.cache(ttl=3600 * 24)
def load_player_data(date_range, agg_metric):
    date_str = date_range.replace(" ", "_")
    df = pd.read_csv(f"data/cache/player-{date_str}-{agg_metric}--grouped.csv")
    return df


@st.cache(ttl=3600 * 24)
def load_play_v_player_data(date_range):
    date_str = date_range.replace(" ", "_")
    play_type_price_data = pd.read_csv(
        f"data/cache/play_v_player-play_type-{date_str}--grouped.csv"
    )
    play_type_tier_price_data = pd.read_csv(
        f"data/cache/play_v_player-play_type_tier-{date_str}--grouped.csv"
    )
    player_tier_price_data = pd.read_csv(
        f"data/cache/play_v_player-player_tier-{date_str}--grouped.csv"
    )
    topN_player_data = pd.read_csv(
        f"data/cache/play_v_player-topN_player-{date_str}--grouped.csv"
    )
    return (
        play_type_price_data,
        play_type_tier_price_data,
        player_tier_price_data,
        topN_player_data,
    )


@st.experimental_memo(ttl=3600 * 24)
def load_challenge_data():
    challenges = pd.read_csv("data/NFLALLDAY_Challenges-Challenges.csv")
    datecols = ["Start Time (EDT)", "End Time (EDT)"]
    challenges[datecols] = challenges[datecols].apply(pd.to_datetime)
    challenges["Index"] = challenges.index
    challenges["Moments Needed"] = challenges["What You'll Need"].apply(
        lambda x: ", ".join(json.loads(x))
    )
    return challenges


@st.experimental_memo(ttl=3600 * 24)
def load_challenge_player_data(challenge):
    challenge_df = pd.read_csv(f"data/challenges/{challenge}.csv.gz")

    challenge_data_points = len(challenge_df)
    challenge_chart_df = challenge_df.astype(str)
    if challenge_data_points > 10000:
        frac = 10000 / challenge_data_points
        weights = 1 / challenge_chart_df.groupby("Display")["Display"].transform(
            "count"
        )
        challenge_chart_df = challenge_chart_df.sample(
            frac=frac,
            weights=weights,
            random_state=1234,
        )

    return challenge_df, challenge_chart_df


@st.experimental_memo(ttl=3600 * 24, suppress_st_warning=True)
def alt_challenge_chart(challenge_chart_df, time_df, shape_col):
    chart = (
        alt.Chart(challenge_chart_df)
        .mark_point(size=50, filled=True)
        .encode(
            x=alt.X("yearmonthdatehoursminutes(Datetime):T", title=None),
            y=alt.Y("Price:Q", scale=alt.Scale(type="log")),
            color=alt.Color(
                "Display",
                title="Player",
                scale=alt.Scale(
                    scheme="category20",
                ),
                sort=["Other"],
            ),
            tooltip=[
                alt.Tooltip("yearmonthdatehoursminutes(Datetime):T", title="Date"),
                "Player",
                alt.Tooltip("Display", title="Player Display"),
                "Moment_Tier",
                "marketplace_id",
                "Serial_Number",
                "Price:Q",
                "Wildcard",
            ],
            shape=alt.Shape(
                shape_col,
                scale=alt.Scale(
                    domain=[
                        "True",
                        "False",
                    ],
                    range=[
                        "circle",
                        "triangle",
                    ],
                ),
            ),
            href="site",
        )
        .interactive()
    )
    date_rules = (
        alt.Chart(
            time_df,
        )
        .mark_rule(strokeDash=[10, 4], opacity=0.7)
        .encode(
            x="yearmonthdatehoursminutes(Datetime):T",
            tooltip=[
                alt.Tooltip("yearmonthdatehoursminutes(Datetime):T", title="Date"),
                alt.Tooltip("Description"),
            ],
            color=alt.Color("Color:N", scale=None),
            strokeWidth=alt.value(3),
        )
    )
    combined = (chart + date_rules).properties(height=600, width=800)
    return combined


@st.experimental_memo(ttl=3600 * 24)
def get_challenge_summary(challenge_df, metric, summary=True):
    sub = challenge_df[challenge_df[metric]]

    if summary:
        sub_n = len(sub)
        sales_count = f"{sub_n}"
        median_price = f"${sub.Price.median():.2f}"
        floor_price = f"${sub.Price.min():.2f}"
        return (
            ("Total Sales Count", sales_count),
            ("Median Price", median_price),
            ("Floor Price", floor_price),
        )
    else:
        grouped_by_nft = sub.groupby("marketplace_id").Price
        sales_count_nft_median = f"{grouped_by_nft.count().median():.2f}"
        mean_price_nft_median = f"${grouped_by_nft.mean().median():.2f}"
        floor_price_nft_median = f"${grouped_by_nft.min().median():.2f}"

        return (
            ("Median Sales Count, per Moment", sales_count_nft_median),
            ("Median Price, per Moment", mean_price_nft_median),
            ("Median Floor Price, per Moment", floor_price_nft_median),
        )


def get_challenge_ttests(challenge_df, use_cache=False, update_cache=False):
    if use_cache and not update_cache:
        with open("data/challenge_ttests.json") as f:
            results = json.load(f)
            return results
    else:
        pre_game = challenge_df[challenge_df["pre_game_1d"]]
        during_game = challenge_df[challenge_df["during_game"]]
        post_game = challenge_df[challenge_df["post_game_1d"]]
        pre_challenge = challenge_df[challenge_df["pre_challenge_1d"]]
        during_challenge = challenge_df[challenge_df["during_challenge"]]
        post_challenge = challenge_df[challenge_df["post_challenge_1d"]]

        pre_game_group_price = pre_game.groupby("marketplace_id").Price.mean()
        during_game_group_price = during_game.groupby("marketplace_id").Price.mean()
        post_game_group_price = post_game.groupby("marketplace_id").Price.mean()
        pre_challenge_group_price = pre_challenge.groupby("marketplace_id").Price.mean()
        during_challenge_group_price = during_challenge.groupby(
            "marketplace_id"
        ).Price.mean()
        post_challenge_group_price = post_challenge.groupby(
            "marketplace_id"
        ).Price.mean()

        pre_game_group_count = pre_game.groupby("marketplace_id").Price.count()
        during_game_group_count = during_game.groupby("marketplace_id").Price.count()
        post_game_group_count = post_game.groupby("marketplace_id").Price.count()
        pre_challenge_group_count = pre_challenge.groupby(
            "marketplace_id"
        ).Price.count()
        during_challenge_group_count = during_challenge.groupby(
            "marketplace_id"
        ).Price.count()
        post_challenge_group_count = post_challenge.groupby(
            "marketplace_id"
        ).Price.count()

        pre_challenge_group_floor = pre_challenge.groupby("marketplace_id").Price.min()
        during_challenge_group_floor = during_challenge.groupby(
            "marketplace_id"
        ).Price.min()
        post_challenge_group_floor = post_challenge.groupby(
            "marketplace_id"
        ).Price.min()

        Before_Game_vs_During_Game_Price = pd.concat(
            [pre_game_group_price, during_game_group_price], axis=1
        )
        Before_Game_vs_During_Game_Count = pd.concat(
            [pre_game_group_count, during_game_group_count], axis=1
        )

        During_Game_vs_During_Challenge_Price = pd.concat(
            [during_game_group_price, during_challenge_group_price], axis=1
        )
        During_Game_vs_During_Challenge_Count = pd.concat(
            [during_game_group_count, during_challenge_group_count], axis=1
        )

        During_Challenge_vs_After_Challenge_Price = pd.concat(
            [during_challenge_group_price, post_challenge_group_price], axis=1
        )
        During_Challenge_vs_After_Challenge_Count = pd.concat(
            [during_challenge_group_count, post_challenge_group_count], axis=1
        )

        Before_Game_vs_After_Game_Price = pd.concat(
            [pre_game_group_price, post_game_group_price], axis=1
        )
        Before_Game_vs_After_Game_Count = pd.concat(
            [pre_game_group_count, post_game_group_count], axis=1
        )

        Before_Challenge_vs_After_Challenge_Price = pd.concat(
            [pre_challenge_group_price, post_challenge_group_price], axis=1
        )
        Before_Challenge_vs_After_Challenge_Count = pd.concat(
            [pre_challenge_group_count, post_challenge_group_count], axis=1
        )

        Before_Challenge_vs_During_Challenge_Count = pd.concat(
            [pre_challenge_group_count, during_challenge_group_count], axis=1
        )
        Before_Challenge_vs_During_Challenge_Price = pd.concat(
            [pre_challenge_group_price, during_challenge_group_price], axis=1
        )

        Before_Challenge_vs_After_Challenge_Floor = pd.concat(
            [pre_challenge_group_floor, post_challenge_group_floor], axis=1
        )
        Before_Challenge_vs_During_Challenge_Floor = pd.concat(
            [pre_challenge_group_floor, during_challenge_group_floor], axis=1
        )

        dfs = {
            "Before_Game_vs_During_Game_Price": Before_Game_vs_During_Game_Price,
            "Before_Game_vs_During_Game_Count": Before_Game_vs_During_Game_Count,
            "During_Game_vs_During_Challenge_Price": During_Game_vs_During_Challenge_Price,
            "During_Game_vs_During_Challenge_Count": During_Game_vs_During_Challenge_Count,
            "During_Challenge_vs_After_Challenge_Price": During_Challenge_vs_After_Challenge_Price,
            "During_Challenge_vs_After_Challenge_Count": During_Challenge_vs_After_Challenge_Count,
            "Before_Game_vs_After_Game_Price": Before_Game_vs_After_Game_Price,
            "Before_Game_vs_After_Game_Count": Before_Game_vs_After_Game_Count,
            "Before_Challenge_vs_After_Challenge_Price": Before_Challenge_vs_After_Challenge_Price,
            "Before_Challenge_vs_After_Challenge_Count": Before_Challenge_vs_After_Challenge_Count,
            "Before_Challenge_vs_During_Challenge_Count": Before_Challenge_vs_During_Challenge_Count,
            "Before_Challenge_vs_During_Challenge_Price": Before_Challenge_vs_During_Challenge_Price,
            "Before_Challenge_vs_After_Challenge_Floor": Before_Challenge_vs_After_Challenge_Floor,
            "Before_Challenge_vs_During_Challenge_Floor": Before_Challenge_vs_During_Challenge_Floor,
        }

        results = {}
        for k, v in dfs.items():
            t = ttest_rel(v.iloc[:, 0], v.iloc[:, 1], nan_policy="omit")
            results[k] = t.pvalue
        if update_cache:
            with open("data/challenge_ttests.json", "w") as f:
                json.dump(results, f)

    return results


def alt_challenge_game(df, xval, yval,):
    base = alt.Chart(df)
    chart = (
        base.mark_point(filled=True, size=100)
        .encode(
            x=alt.X(
                "jitter:Q",
                title=None,
                axis=alt.Axis(values=[0], ticks=True, grid=False, labels=False),
                scale=alt.Scale(),
            ),
            y=alt.Y(f"{yval}:Q", scale=alt.Scale(type="log", zero=False, nice=False)),
            tooltip=[
                "Player:N",
                "Team:N",
                "Position:N",
                "Moment_Tier:N",
                "Price:Q",
                "Count:Q",
                "Floor:Q"
            ],
            color=alt.Color(
                "Display:N",
                title="Player",
                scale=alt.Scale(
                    scheme="category20",
                ),
                sort=["Other"],
            ),
            shape=alt.Shape(
                "Moment_Tier",
                scale=alt.Scale(
                    domain=[
                        "True",
                        "False",
                    ],
                    range=[
                        "circle",
                        "triangle",
                    ],
                ),
            ),
            href="site",
        )
        .transform_calculate(
            # Generate Gaussian jitter with a Box-Muller transform
            jitter="sqrt(-2*log(random()))*cos(2*PI*random())"
        )
        .interactive()
        .properties(height=800, width=125)
    )
    box = base.mark_boxplot(color="#004D40", outliers=False, size=25).encode(
        y=alt.Y(f"{yval}:Q"),
    )
    combined_chart = (
        alt.layer(box, chart)
        .facet(
            column=alt.Column(
                f"{xval}:N",
                title=None,
                header=alt.Header(
                    labelAngle=-90,
                    titleOrient="top",
                    labelOrient="bottom",
                    labelAlign="right",
                    labelPadding=3,
                ),
                # sort=position_type_dict[position_type][1],
            ),
            title=f'{xval.title().replace("_", " ")}: {yval}',
        )
        .configure_facet(spacing=0)
    )
    return combined_chart


@st.experimental_memo(ttl=3600 * 24, suppress_st_warning=True)
def load_challenge_reward():
    return pd.read_csv("data/NFLALLDAY_Challenges-RewardBreakdown.csv")
