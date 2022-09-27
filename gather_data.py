#!/usr/bin/env python3

from datetime import datetime
from functools import partial
from pathlib import Path

import nfl_data_py as nfl
import numpy as np
import pandas as pd
import streamlit as st
from jinja2 import Environment, FileSystemLoader
from shroomdk import ShroomDK
from streamlit.type_util import Key

teams = [
    "Arizona Cardinals",
    "Atlanta Falcons",
    "Baltimore Ravens",
    "Buffalo Bills",
    "Carolina Panthers",
    "Chicago Bears",
    "Cincinnati Bengals",
    "Cleveland Browns",
    "Dallas Cowboys",
    "Denver Broncos",
    "Detroit Lions",
    "Green Bay Packers",
    "Houston Texans",
    "Indianapolis Colts",
    "Jacksonville Jaguars",
    "Kansas City Chiefs",
    "Las Vegas Raiders",
    "Los Angeles Chargers",
    "Los Angeles Raiders",
    "Los Angeles Rams",
    "Miami Dolphins",
    "Minnesota Vikings",
    "New England Patriots",
    "New Orleans Saints",
    "New York Giants",
    "New York Jets",
    "Oakland Raiders",
    "Philadelphia Eagles",
    "Phoenix Cardinals",
    "Pittsburgh Steelers",
    "San Francisco 49ers",
    "Seattle Seahawks",
    "St. Louis Rams",
    "Tampa Bay Buccaneers",
    "Tennessee Oilers",
    "Tennessee Titans",
    "Washington Football Team",
]

pbp_fields = fields = [
    "play_id",
    "game_id",
    "home_team",
    "away_team",
    "week",
    "qtr",
    "quarter_seconds_remaining",
    "sack",
    "touchdown",
    "pass_touchdown",
    "rush_touchdown",
    "return_touchdown",
    "interception",
    "safety",
    "tackled_for_loss",
    "fumble_lost",
    "first_down",
]


API_KEY = st.secrets["flipside"]["api_key"]
sdk = ShroomDK(API_KEY)


def get_query(team):
    env = Environment(loader=FileSystemLoader("./sql"))
    template = env.get_template("sdk_allday.sql")
    query = template.render({"team": f"'{team}'"})
    return query


def get_datetime_string():
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d")
    return dt_string


def get_flipside_team_data(team, save=True):
    query = get_query(team)
    query_result_set = sdk.query(query)
    df = pd.DataFrame(query_result_set.rows, columns=query_result_set.columns)
    if save:
        dt_string = get_datetime_string()
        output_dir = Path(f"data/{dt_string}")
        output_dir.mkdir(exist_ok=True)
        df.to_csv(
            f"{output_dir}/{dt_string}_{team.replace(' ', '_')}.csv.gz",
            index=False,
            compression="gzip",
        )
    return df


def combine_flipside_data(data_dir):
    d = Path(data_dir)
    data_files = d.glob("*.csv.gz")
    dfs = []

    for x in data_files:
        df = pd.read_csv(x)
        dfs.append(df)

    combined_df = (
        pd.concat(dfs).sort_values(by=["Date", "Player"]).reset_index(drop=True)
    )

    return combined_df


def get_years_after_date(years, cutoff):
    return [x for x in years if x >= cutoff]


def scored_td(row, df, data_type, team_lookup=None):
    if row.Set_Name == "Move the Chains":
        return False
    if row.Play_Type not in [
        "Pass",
        "Reception",
        "Rush",
        "Strip Sack",
        "Interception",
        "Fumble Recovery",  # ~50% TD
        "Blocked Kick",  # 1/4 not td
        "Punt Return",  # all TD
        "Kick Return",  # 1/6 not td
    ]:
        return False
    if int(row.Season) < 1999:
        return None

    szn = row.Season
    wk = row.Week
    pt = row.Play_Type
    player = row.Player

    try:
        wk = int(wk)
    except ValueError:
        if wk == "Divisional":
            wk = 20
        elif wk == "Super Bowl LVI":
            wk = 22
        else:
            wk = np.nan

    if data_type == "stats":
        player_stats = df[
            (df.season == szn) & (df.player_display_name == player) & (df.week == wk)
        ]
        if row.Set_Name == "Move the Chains":
            return False
        elif pt == "Reception":
            td_type = "receiving_tds"
        elif pt == "Rush":
            td_type = "rushing_tds"
        elif pt == "Pass":
            td_type = "passing_tds"
        else:
            return None
        try:
            return (player_stats[td_type] >= 1).values[0]
        except IndexError:
            return None

    elif data_type == "pbp":
        # manual checks while debugging:
        if row.unique_id in [
            "2399701d-d4a9-4a5c-9449-a5df10712c2b",  # Mac Jones TD with wrong time
            "3039dc31-e09a-4e53-90c7-4b8e928ae947",  # LF TD
            "383c3543-35dc-4945-b164-77a9a0f9a8f7",  # INT returned for TD
            "577e4e69-a24d-478a-b44b-da6b8e56cb93",
            "bae9227d-37f6-4e80-b967-dbb0a79af207",
            "b753616b-ad92-4474-81da-55137a9bb2f9",
            "f24046e7-787c-4512-8e69-718b8168de90",
            "8efdacdc-d39f-4cbe-987c-d14257324e3c",
            "ee5a2e00-4371-42b4-ac0b-eda0a9d8ff49",
            "f24046e7-787c-4512-8e69-718b8168de90",
        ]:
            return True
        elif row.unique_id in [
            "773ac906-ef38-499a-9f19-d77bd69c50f3",
            "db2a1785-4062-4e80-9f6f-a7d701714378",
            "8a84c558-3a7e-4365-b38a-eac93187a1b7",
            "be88ed33-7001-4e90-af2d-a9a2a386411c",
        ]:
            return False
        else:
            try:
                home_team = team_lookup[row.Home_Team_Name]
            except KeyError:
                return None
            qtr = row.Quarter
            time_left = convert_timestr(row.Time)

            # try:
            play = df[
                (df["home_team"] == home_team)
                & (df["years"] == szn)  # TODO: change to Season
                & (df["week"] == wk)
                & (df["qtr"] == qtr)
                & (df["quarter_seconds_remaining"] == time_left)
            ]

            if len(play) == 0:
                return None
            elif len(play) == 1:
                td = play.touchdown.values[0]
            else:
                td = play.iloc[-1].touchdown
            return bool(td)


def convert_timestr(time):
    try:
        m, s = time.split(":")
    except (AttributeError, ValueError):
        return None

    min2sec = int(m) * 60 if len(m) > 0 else 0
    return min2sec + int(s)


def scored_td_in_game(row):
    if not pd.isna(row.pbp_td):
        return row.pbp_td
    if not pd.isna(row.game_td):
        return row.game_td
    else:
        return row.description_td


def scored_td_in_moment(row):
    if not pd.isna(row.pbp_td):
        return row.pbp_td
    if row.game_td is False:
        return False
    else:
        return row.description_td


def get_td_data(score_data, weekly_df, pbp_df, team_abbr):
    score_data["description_td"] = score_data.Moment_Description.str.contains(
        "td | touchdown", regex=True, case=False
    ) & (score_data.Set_Name != "Move the Chains")

    unique_plays = score_data.groupby("unique_id").first().reset_index()

    game_td_func = partial(scored_td, df=weekly_df, data_type="stats")
    pbp_td_func = partial(scored_td, df=pbp_df, data_type="pbp", team_lookup=team_abbr)
    unique_plays["game_td"] = unique_plays.apply(
        game_td_func,
        axis=1,
    )
    unique_plays["pbp_td"] = unique_plays.apply(pbp_td_func, axis=1)

    score_data = score_data.merge(
        unique_plays[["unique_id", "game_td", "pbp_td"]], on="unique_id"
    ).reset_index(drop=True)

    score_data["scored_td_in_game"] = score_data.apply(scored_td_in_game, axis=1)
    score_data["scored_td_in_moment"] = score_data.apply(scored_td_in_moment, axis=1)

    return score_data


if __name__ == "__main__":

    for team in teams:
        print(f"Getting data for {team}...")
        get_flipside_team_data(team)

    data_dir = Path("data", get_datetime_string())
    df = combine_flipside_data(data_dir)
    sales_counts = (
        df.groupby("NFT_ID")["tx_id"]
        .count()
        .reset_index()
        .sort_values(by="tx_id")
        .rename(columns={"tx_id": "Sales_Count"})
    )
    df = df.merge(sales_counts, on="NFT_ID")
    df["Resell_Number"] = df.groupby("NFT_ID")["tx_id"].cumcount()

    # #@# just saving file with TD data now
    # df.to_csv(
    #     "data/current_allday_data.csv.gz",
    #     index=False,
    #     compression="gzip",
    # )
    # @# debugging
    # df = pd.read_csv(
    #     "data/current_allday_data.csv.gz",
    # )
    # weekly_data = pd.read_csv(
    #     "data/weekly_data.csv",
    # )
    # pbp_data = pd.read_csv(
    #     "data/pbp.csv.gz",
    # )
    # --

    years = df.Season.unique().tolist()
    if 2022 not in years:
        years.append(2022)

    team_desc = nfl.import_team_desc()
    team_desc.to_csv("data/team_desc.csv", index=False)

    team_abbr = dict(team_desc[["team_name", "team_abbr"]].values.tolist())
    team_abbr["Washington Football Team"] = "WAS"
    team_abbr["Los Angeles Rams"] = "LA"  # not sure why this is just a 2 letter abbrev

    weekly_data = nfl.import_weekly_data(get_years_after_date(years, 1999))
    weekly_data.to_csv("data/weekly_data.csv", index=False)

    pbp_data = nfl.import_pbp_data(get_years_after_date(years, 1999), columns=fields)
    pbp_data = pd.read_csv("data/pbp.csv.gz")
    pbp_data["Season"] = pbp_data.game_id.str.split("_").str[0]
    pbp_data.to_csv(
        "data/pbp.csv.gz",
        index=False,
        compression="gzip",
    )

    main_with_td = get_td_data(df, weekly_data, pbp_data, team_abbr)
    main_with_td.to_csv(
        "data/current_allday_data.csv.gz",
        index=False,
        compression="gzip",
    )

    roster_data = nfl.import_rosters(get_years_after_date(years, 1999))
    roster_data.to_csv("data/roster_data.csv", index=False)

    season_data = nfl.import_seasonal_data(get_years_after_date(years, 1999))
    season_data.to_csv("data/season_data.csv", index=False)

    snap_data = nfl.import_snap_counts(get_years_after_date(years, 2012))
    snap_data.to_csv("data/snap_data.csv", index=False)

    for x in ["weekly", "season"]:
        df = nfl.import_qbr(get_years_after_date(years, 2006), frequency=x)
        df.to_csv(f"data/qbr_data_{x}.csv", index=False)

    for x in ["receiving", "passing", "rushing"]:
        df = nfl.import_ngs_data(x, get_years_after_date(years, 2019))
        df.to_csv(f"data/ngs_data_{x}.csv", index=False)

    for x in ["pass", "rec", "rush"]:
        df = nfl.import_pfr(x, get_years_after_date(years, 2019))
        df.to_csv(f"data/pfr_data_{x}.csv", index=False)

    schedule_data = nfl.import_schedules(get_years_after_date(years, 1999))
    schedule_data.to_csv("data/schedule_data.csv", index=False)
