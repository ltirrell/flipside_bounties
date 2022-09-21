#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path

import nfl_data_py as nfl
import pandas as pd
import streamlit as st
from jinja2 import Environment, FileSystemLoader
from shroomdk import ShroomDK

teams = [
    "Cleveland Browns",
    "Tennessee Oilers",
    "Arizona Cardinals",
    "New Orleans Saints",
    "Carolina Panthers",
    "St. Louis Rams",
    "Detroit Lions",
    "Pittsburgh Steelers",
    "Chicago Bears",
    "Tampa Bay Buccaneers",
    "Green Bay Packers",
    "Cincinnati Bengals",
    "Tennessee Titans",
    "Indianapolis Colts",
    "New York Giants",
    "Kansas City Chiefs",
    "San Francisco 49ers",
    "Los Angeles Rams",
    "Atlanta Falcons",
    "Houston Texans",
    "Las Vegas Raiders",
    "New England Patriots",
    "Oakland Raiders",
    "Baltimore Ravens",
    "Denver Broncos",
    "Jacksonville Jaguars",
    "Los Angeles Chargers",
    "New York Jets",
    "Philadelphia Eagles",
    "Phoenix Cardinals",
    "Los Angeles Raiders",
    "Dallas Cowboys",
    "Minnesota Vikings",
    "Miami Dolphins",
    "Washington Football Team",
    "Buffalo Bills",
    "Seattle Seahawks",
]

years = [2022]

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


if __name__ == "__main__":

    for team in teams:
        print(f"Getting data for {team}...")
        get_flipside_team_data(team)

    data_dir = Path("data", get_datetime_string())
    df = combine_flipside_data(data_dir)
    df.to_csv(
        "data/current_allday_data.csv.gz",
        index=False,
        compression="gzip",
    )

    team_desc = nfl.import_team_desc()
    team_desc.to_csv("data/team_desc.csv", index=False)

    weekly_data = nfl.import_weekly_data(years)
    weekly_data.to_csv("data/weekly_data.csv", index=False)

    roster_data = nfl.import_rosters(years)
    roster_data.to_csv("data/roster_data.csv", index=False)

    season_data = nfl.import_seasonal_data(years)
    season_data.to_csv("data/season_data.csv", index=False)

    snap_data = nfl.import_snap_counts(years)
    snap_data.to_csv("data/snap_data.csv", index=False)

    for x in ["weekly", "season"]:
        df = nfl.import_qbr(years, frequency=x)
        df.to_csv(f"data/qbr_data_{x}.csv", index=False)

    for x in ["receiving", "passing", "rushing"]:
        df = nfl.import_ngs_data(x, years)
        df.to_csv(f"data/ngs_data_{x}.csv", index=False)

    for x in ["pass", "rec", "rush"]:
        df = nfl.import_pfr(x, years)
        df.to_csv(f"data/pfr_data_{x}.csv", index=False)
