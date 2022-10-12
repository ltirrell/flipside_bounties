#!/usr/bin/env python3

import datetime
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import nfl_data_py as nfl
import numpy as np
import pandas as pd
import streamlit as st
from jinja2 import Environment, FileSystemLoader
from shroomdk import ShroomDK

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

pbp_fields = [
    "fumble",
    "away_team",
    "first_down",
    "fumble_lost",
    "game_id",
    "home_team",
    "interception",
    "pass_touchdown",
    "play_id",
    "qtr",
    "quarter_seconds_remaining",
    "return_touchdown",
    "rush_touchdown",
    "sack",
    "safety",
    "tackled_for_loss",
    "touchdown",
    "week",
    "complete_pass",
    "fantasy_player_id",
    "fantasy_player_name",
    "forced_fumble_player_1_player_id",
    "forced_fumble_player_1_player_name",
    "forced_fumble_player_1_team",
    "forced_fumble_player_2_player_id",
    "forced_fumble_player_2_player_name",
    "forced_fumble_player_2_team",
    "fumble_recovery_1_player_id",
    "fumble_recovery_1_player_name",
    "fumble_recovery_1_team",
    "fumble_recovery_1_yards",
    "fumble_recovery_2_player_id",
    "fumble_recovery_2_player_name",
    "fumble_recovery_2_team",
    "fumble_recovery_2_yards",
    "fumbled_1_player_id",
    "fumbled_1_player_name",
    "fumbled_1_team",
    "fumbled_2_player_id",
    "fumbled_2_player_name",
    "fumbled_2_team",
    "half_sack_1_player_id",
    "half_sack_1_player_name",
    "half_sack_2_player_id",
    "half_sack_2_player_name",
    "interception_player_id",
    "interception_player_name",
    "kicker_player_id",
    "kicker_player_name",
    "kickoff_returner_player_id",
    "kickoff_returner_player_name",
    "passer_player_id",
    "passer_player_name",
    "passing_yards",
    "punt_returner_player_id",
    "punt_returner_player_name",
    "punter_player_id",
    "punter_player_name",
    "receiver_player_id",
    "receiver_player_name",
    "receiving_yards",
    "rusher_player_id",
    "rusher_player_name",
    "rushing_yards",
    "sack_player_id",
    "sack_player_name",
    "safety_player_id",
    "safety_player_name",
]

rarity_dict = {"COMMON": 0, "RARE": 1, "LEGENDARY": 2, "ULTIMATE": 3}

all_dates = [
    f"{x:%Y-%m-%d}"
    for x in pd.date_range(
        datetime.date(2021, 12, 10), (datetime.datetime.today() - pd.Timedelta("1d"))
    )
]

API_KEY = st.secrets["flipside"]["api_key"]
sdk = ShroomDK(API_KEY)


def get_team_query(team):
    env = Environment(loader=FileSystemLoader("./sql"))
    template = env.get_template("sdk_allday.sql")
    query = template.render({"team": f"'{team}'"})
    return query


def get_date_query(date, sql_file):
    env = Environment(loader=FileSystemLoader("./sql"))
    template = env.get_template(sql_file)
    query = template.render({"date": f"'{date}'"})
    return query


def get_datetime_string():
    now = datetime.datetime.now()
    dt_string = now.strftime("%Y-%m-%d")
    return dt_string


def get_flipside_team_data(team, save=True):
    print(f"Getting data for {team}...")
    dt_string = get_datetime_string()
    output_dir = Path(f"data/{dt_string}")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir/ f"{dt_string}_team--{team.replace(' ', '_')}.csv.gz"
    if not output_file.exists():
        query = get_team_query(team)
        query_result_set = sdk.query(query)
        df = pd.DataFrame(query_result_set.rows, columns=query_result_set.columns)
        if save:
            print(f"Saving {output_file}...")
            df.to_csv(
                output_file,
                index=False,
                compression="gzip",
            )
    else:
        return output_file
    return df


def get_flipside_pack_data(date, sql_file, output_str, save=True):
    # dt_string = get_datetime_string()  # No longer using date
    output_dir = Path(f"data/packs")
    output_file = output_dir / f"{output_str}--{date.replace(' ', '_')}.csv.gz"
    if not output_file.exists():
        print(f"Getting data for {date}...")
        query = get_date_query(date, sql_file)
        query_result_set = sdk.query(query)
        df = pd.DataFrame(query_result_set.rows, columns=query_result_set.columns)
        if save:
            output_dir.mkdir(exist_ok=True)
            print(f"Saving {output_file}...")
            df.to_csv(
                output_file,
                index=False,
                compression="gzip",
            )
    else:
        print(f"#@# Using cached file: {output_file} ...")
    return output_file


def combine_flipside_data(data_dir, glob_str, sort_by):
    d = Path(data_dir)
    data_files = d.glob(glob_str)
    dfs = []

    for x in data_files:
        df = pd.read_csv(x)
        dfs.append(df)

    combined_df = pd.concat(dfs).sort_values(by=sort_by).reset_index(drop=True)

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
                & (df["Season"] == szn)
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


def get_td_data(df, weekly_df, pbp_df, team_abbr):
    df["description_td"] = df.Moment_Description.str.contains(
        "td | touchdown", regex=True, case=False
    ) & (df.Set_Name != "Move the Chains")

    unique_plays = df.groupby("unique_id").first().reset_index()

    game_td_func = partial(scored_td, df=weekly_df, data_type="stats")
    pbp_td_func = partial(scored_td, df=pbp_df, data_type="pbp", team_lookup=team_abbr)
    unique_plays["game_td"] = unique_plays.apply(
        game_td_func,
        axis=1,
    )
    unique_plays["pbp_td"] = unique_plays.apply(pbp_td_func, axis=1)

    df = df.merge(
        unique_plays[["unique_id", "game_td", "pbp_td"]], on="unique_id"
    ).reset_index(drop=True)

    df["scored_td_in_game"] = df.apply(scored_td_in_game, axis=1)
    df["scored_td_in_moment"] = df.apply(scored_td_in_moment, axis=1)

    return df


def won_game(row):
    team = row.Team
    home_team = row.Home_Team_Name
    home_team_score = int(row.Home_Team_Score)
    away_team_score = int(row.Away_Team_Score)

    home_team_won = home_team_score > away_team_score

    if team == home_team:
        return home_team_won
    else:
        return not home_team_won


def tie_game(row):
    home_team_score = int(row.Home_Team_Score)
    away_team_score = int(row.Away_Team_Score)
    return home_team_score == away_team_score


def get_game_outcome(row):
    if row.tie_game:
        return "Tie"
    if row.won_game:
        return "Win"
    else:
        return "Loss"


if __name__ == "__main__":
    # #TODO: turn on when updating
    pack_dir = Path("data/packs")
    with Pool(16) as p:
        pack_data_func = partial(
            get_flipside_pack_data, sql_file="sdk_packs.sql", output_str="pack_sales"
        )
        p.map(pack_data_func, all_dates)

        reveals_func = partial(
            get_flipside_pack_data,
            sql_file="sdk_reveals.sql",
            output_str="pack_reveals",
        )
        p.map(reveals_func, all_dates)

    pack_df = combine_flipside_data(
        pack_dir, f"*pack_sales--*csv.gz", ["Datetime", "Price"]
    )
    # #HACK: empirically found prices for Standard v Premium, PLAYOFFS grouped in with Standard
    pack_df['Pack Type'] = pack_df.Price.apply(lambda x: 'Standard' if x < 79 or x == 84 else 'Premium')
    pack_df.to_csv(
        "data/pack_data.csv.gz",
        index=False,
        compression="gzip",
    )
    reveal_df = combine_flipside_data(pack_dir, f"*pack_reveals--*csv.gz", ["Datetime"])
    reveal_df.to_csv(
        "data/pack_reveals.csv.gz",
        index=False,
        compression="gzip",
    )

    combined_df = reveal_df.copy()
    combined_df["NFTS"] = combined_df.NFTS.str.split(",")
    combined_df["Moments_In_Pack"] = combined_df.NFTS.str.len()
    combined_df = combined_df.rename(
        columns={
            "NFTS": "Moment_ID",
            "PACK_ID": "Pack_ID",
            "Datetime": "Datetime_Reveal",
            "tx_id": "tx_id_Reveal",
        }
    )
    combined_df = combined_df.explode("Moment_ID")
    combined_df["Moment_ID"] = combined_df["Moment_ID"].str.split(".AllDay.").str[-1]
    combined_df = combined_df.merge(
        pack_df, left_on="Pack_ID", right_on="NFT_ID", how="left"
    )
    combined_df["Moment_ID"] = pd.to_numeric(combined_df["Moment_ID"])
    combined_df = combined_df.rename(
        columns={
            "Price": "Pack_Price",
            "Datetime": "Datetime_Pack",
            "tx_id": "tx_id_Pack",
            "Buyer": "Pack_Buyer",
        }
    ).drop(columns="NFT_ID")
    combined_df.to_csv(
        "data/pack_combined.csv.gz",
        index=False,
        compression="gzip",
    )

    data_dir = Path("data", get_datetime_string())
    with Pool(16) as p:
        p.map(get_flipside_team_data, teams)

    df = combine_flipside_data(data_dir, f"*_team--*csv.gz",["Date", "Player"])
    sales_counts = (
        df.groupby("NFT_ID")["tx_id"]
        .count()
        .reset_index()
        .sort_values(by="tx_id")
        .rename(columns={"tx_id": "Sales_Count"})
    )
    df = df.merge(sales_counts, on="NFT_ID")
    df["Resell_Number"] = df.groupby("NFT_ID")["tx_id"].cumcount()
    df["Rarity"] = df.apply(lambda x: rarity_dict[x.Moment_Tier], axis=1)

    all_day_debuts = (
        df[df.Position != "Team"].groupby("Player").marketplace_id.min().reset_index()
    )
    all_day_debuts["all_day_debut"] = 1
    df = df.merge(all_day_debuts, on=["marketplace_id", "Player"], how="left")
    df.loc[df.all_day_debut.isna(), "all_day_debut"] = 0
    df["rookie_year"] = df.Season == df.Rookie_Year
    df["rookie_mint"] = df.apply(
        lambda x: (x.Series == "Series 1" and x.Rookie_Year == 2021)
        or (x.Series == "Series 2" and x.Rookie_Year == 2022),
        axis=1,
    )
    # #@# debugging
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

    schedule_data = nfl.import_schedules(get_years_after_date(years, 1999))
    schedule_data.to_csv("data/schedule_data.csv", index=False)

    weekly_data = nfl.import_weekly_data(get_years_after_date(years, 1999))
    weekly_data.to_csv("data/weekly_data.csv", index=False)

    # #TODO: turn on when updating
    nfl.cache_pbp(
        get_years_after_date(years, 1999),
        downcast=False,
    )
    pbp_data = nfl.import_pbp_data(
        get_years_after_date(years, 1999),
        downcast=False,
        cache=True
        # columns=pbp_fields  # no longer using fields
    )
    pbp_data["Season"] = pd.to_numeric(pbp_data.game_id.str.split("_").str[0])

    pbp_data.to_csv(
        "data/pbp.csv.gz",
        index=False,
        compression="gzip",
    )
    pbp_2022 = pbp_data[pbp_data.Season == 2022].reset_index(drop=True)
    pbp_2022.to_csv("data/pbp_2022.csv.gz", index=False, compression="gzip")

    main_with_td = get_td_data(df, weekly_data, pbp_data, team_abbr)
    # #TODO: eventually add gambling lines etc info from schedule_data
    main_with_td["won_game"] = main_with_td.apply(won_game, axis=1)
    main_with_td["tie_game"] = main_with_td.apply(tie_game, axis=1)
    main_with_td["Game Outcome"] = main_with_td.apply(get_game_outcome, axis=1)
    main_with_td.to_csv(
        "data/current_allday_data.csv.gz",
        index=False,
        compression="gzip",
    )

    merged = main_with_td.merge(
        combined_df[
            [
                "Datetime_Reveal",
                "Moment_ID",
                "Moments_In_Pack",
                "Datetime_Pack",
                "Pack_Price",
                "Pack_Buyer",
                "Pack Type",
            ]
        ],
        how="outer",
        left_on="NFT_ID",
        right_on="Moment_ID",
    )

    merged.to_csv(
        "data/current_allday_data_pack.csv.gz",
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
