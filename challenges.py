#!/usr/bin/env python3

from collections import defaultdict
import pandas as pd
import json

from utils import *

from warnings import simplefilter

simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)

df = pd.read_csv("data/current_allday_data.csv.gz")
datecols = ["Datetime", "Date", "Moment_Date"]
df[datecols] = df[datecols].apply(pd.to_datetime)

challenges = pd.read_csv("data/NFLALLDAY_Challenges-Challenges.csv")
datecols = ["Start Time (EDT)", "End Time (EDT)"]
challenges[datecols] = challenges[datecols].apply(pd.to_datetime)
challenges["Index"] = challenges.index
challenges["Moments Needed"] = challenges["What You'll Need"].apply(
    lambda x: ", ".join(json.loads(x))
)

weekly_df, season_df = load_stats_data(2022)
weekly_df["total_yards"] = weekly_df.apply(
    lambda x: x.passing_yards + x.receiving_yards + x.rushing_yards, axis=1
)

pbp = pd.read_csv("data/pbp_2022.csv.gz")

roster_df = pd.read_csv("data/roster_data.csv")
roster_df = roster_df[roster_df.season == 2022].reset_index(drop=True)


def get_top_n_players(
    df,
    n,
    positions=["QB", "RB", "WR", "TE"],
    return_df=False,
    by_total=True,
    by_recieving=False,
    qb_passing=True,
):
    if by_total:
        players = (
            df[df.position.isin(positions)][
                ["player_display_name", "position", "total_yards"]
            ]
            .sort_values(by="total_yards", ascending=False)
            .groupby("position")
            .head(n)
            .sort_values(by=["position", "total_yards"], ascending=False)
            .reset_index(drop=True)
        )
        players = players.rename(columns={"total_yards": "yards"})
    elif by_recieving:
        players = (
            df[df.position.isin(positions)][
                ["player_display_name", "position", "receiving_yards"]
            ]
            .sort_values(by="receiving_yards", ascending=False)
            .groupby("position")
            .head(n)
            .sort_values(by=["position", "receiving_yards"], ascending=False)
            .reset_index(drop=True)
        )
        players = players.rename(columns={"receiving_yards": "yards"})
        if qb_passing:
            qb = (
                df[df.position == "QB"][
                    ["player_display_name", "position", "passing_yards"]
                ]
                .sort_values(by="passing_yards", ascending=False)
                .groupby("position")
                .head(n)
                .sort_values(by=["position", "passing_yards"], ascending=False)
                .reset_index(drop=True)
            )
            qb = qb.rename(columns={"passing_yards": "yards"})
            players = players[players.position != "QB"]
            players = pd.concat([players, qb]).reset_index(drop=True)

    if return_df:
        return players
    return players.player_display_name.values


def get_def_df(df, roster_df):
    sack = defaultdict(float)
    fumble = defaultdict(float)
    interception = defaultdict(float)
    tackle = defaultdict(float)
    tfl = defaultdict(float)

    for _, x in df.iterrows():
        if not pd.isna(x.half_sack_1_player_id):
            sack[x.half_sack_1_player_id] += 0.5
        if not pd.isna(x.half_sack_2_player_id):
            sack[x.half_sack_2_player_id] += 0.5
        if not pd.isna(x.sack_player_id):
            sack[x.sack_player_id] += 1

        if not pd.isna(x.forced_fumble_player_1_player_id):
            fumble[x.forced_fumble_player_1_player_id] += 1
        if not pd.isna(x.forced_fumble_player_2_player_id):
            fumble[x.forced_fumble_player_2_player_id] += 1

        if not pd.isna(x.interception_player_id):
            interception[x.interception_player_id] += 1

        if not pd.isna(x.tackle_for_loss_1_player_id):
            tackle[x.tackle_for_loss_1_player_id] += 1
            tfl[x.tackle_for_loss_1_player_id] += 1
        if not pd.isna(x.tackle_for_loss_2_player_id):
            tackle[x.tackle_for_loss_2_player_id] += 1
            tfl[x.tackle_for_loss_2_player_id] += 1
        if not pd.isna(x.solo_tackle_1_player_id):
            tackle[x.solo_tackle_1_player_id] += 1
        if not pd.isna(x.solo_tackle_2_player_id):
            tackle[x.solo_tackle_2_player_id] += 1
        if not pd.isna(x.assist_tackle_1_player_id):
            tackle[x.assist_tackle_1_player_id] += 1
        if not pd.isna(x.assist_tackle_2_player_id):
            tackle[x.assist_tackle_2_player_id] += 1
        if not pd.isna(x.assist_tackle_3_player_id):
            tackle[x.assist_tackle_3_player_id] += 1
        if not pd.isna(x.assist_tackle_4_player_id):
            tackle[x.assist_tackle_4_player_id] += 1
        if not pd.isna(x.tackle_with_assist_1_player_id):
            tackle[x.tackle_with_assist_1_player_id] += 1
        if not pd.isna(x.tackle_with_assist_2_player_id):
            tackle[x.tackle_with_assist_2_player_id] += 1

    interception_df = pd.DataFrame.from_dict(
        interception, orient="index", columns=["interception"]
    )
    fumble_df = pd.DataFrame.from_dict(fumble, orient="index", columns=["fumble"])
    sack_df = pd.DataFrame.from_dict(sack, orient="index", columns=["sack"])
    tackle_df = pd.DataFrame.from_dict(tackle, orient="index", columns=["tackle"])
    tfl_df = pd.DataFrame.from_dict(tfl, orient="index", columns=["tfl"])

    def_df = (
        pd.concat([interception_df, fumble_df, sack_df, tackle_df, tfl_df])
        .groupby(level=0)
        .sum()
    )

    def_df = (
        def_df.merge(
            roster_df[["player_id", "player_name", "team", "position"]],
            left_index=True,
            right_on="player_id",
        )
        .sort_values(
            by=["sack", "interception", "fumble", "tfl", "tackle"], ascending=False
        )
        .reset_index(drop=True)
    )
    return def_df


def get_top_n_players(
    df,
    n,
    positions=["QB", "RB", "WR", "TE"],
    return_df=False,
    by_total=True,
    by_recieving=False,
    qb_passing=True,
):
    if by_total:
        players = (
            df[df.position.isin(positions)][
                ["player_display_name", "position", "total_yards"]
            ]
            .sort_values(by="total_yards", ascending=False)
            .groupby("position")
            .head(n)
            .sort_values(by=["position", "total_yards"], ascending=False)
            .reset_index(drop=True)
        )
        players = players.rename(columns={"total_yards": "yards"})
    elif by_recieving:
        players = (
            df[df.position.isin(positions)][
                ["player_display_name", "position", "receiving_yards"]
            ]
            .sort_values(by="receiving_yards", ascending=False)
            .groupby("position")
            .head(n)
            .sort_values(by=["position", "receiving_yards"], ascending=False)
            .reset_index(drop=True)
        )
        players = players.rename(columns={"receiving_yards": "yards"})
        if qb_passing:
            qb = (
                df[df.position == "QB"][
                    ["player_display_name", "position", "passing_yards"]
                ]
                .sort_values(by="passing_yards", ascending=False)
                .groupby("position")
                .head(n)
                .sort_values(by=["position", "passing_yards"], ascending=False)
                .reset_index(drop=True)
            )
            qb = qb.rename(columns={"passing_yards": "yards"})
            players = players[players.position != "QB"]
            players = pd.concat([players, qb]).reset_index(drop=True)

    if return_df:
        return players
    return players.player_display_name.values


def get_player_display(df, n=19):
    players = df.Player.value_counts().index[:n].to_list()
    display = df.Player.apply(lambda x: x if x in players else "Other")
    return display


# --- Week 1
w01_def_pbp = pbp[
    (pbp.week == 1)
    & (
        (pbp.sack == 1)
        | (pbp.fumble == 1)
        | (pbp.interception == 1)
        | (pbp.solo_tackle == 1)
        | (pbp.tackled_for_loss == 1)
        | (pbp.assist_tackle == 1)
        | (pbp.tackle_with_assist == 1)
    )
][
    [
        "home_team",
        "away_team",
        "half_sack_1_player_id",
        "half_sack_2_player_id",
        "sack_player_id",
        "forced_fumble_player_1_player_id",
        "forced_fumble_player_2_player_id",
        "interception_player_id",
        "tackle_for_loss_1_player_id",
        "tackle_for_loss_2_player_id",
        "solo_tackle_1_player_id",
        "solo_tackle_2_player_id",
        "assist_tackle_1_player_id",
        "assist_tackle_2_player_id",
        "assist_tackle_3_player_id",
        "assist_tackle_4_player_id",
        "tackle_with_assist_1_player_id",
        "tackle_with_assist_2_player_id",
    ]
]
w01_def = get_def_df(w01_def_pbp, roster_df)


w01_thursday = df[
    (df.Player.isin(["Cooper Kupp", "Gabriel Davis", "Stefon Diggs"]))
    | (
        (df.Position.isin(defense))
        & (df.Team.isin(["Buffalo Bills", "Los Angeles Rams"]))
    )
]
w01_thursday["Display"] = get_player_display(w01_thursday)
w01_thursday["Challenge Type"] = "w01_thursday"
w01_thursday["Wildcard"] = False

w01_slate = df[
    df.Player.isin(
        [
            "Saquon Barkley",
            "Jonathan Taylor",
            "D'Andre Swift",
            "Nick Chubb",
            "Cordarrelle Patterson",
        ]
    )
    | (df["all_day_debut"] == 1)
]

w01_slate["Display"] = get_player_display(w01_slate)
w01_slate["Challenge Type"] = "w01_slate"
w01_slate["Wildcard"] = w01_slate["all_day_debut"]


w01_sunday_night = df[
    df.Player.isin(["Julio Jones"])
    | (
        df.Player.isin(
            weekly_df[
                (weekly_df.week == 1)
                & (weekly_df.team.isin(["TB", "DAL"]))
                & (weekly_df.receptions >= 1)
            ].player_display_name.values
        )
    )
]
w01_sunday_night["Display"] = get_player_display(w01_sunday_night)
w01_sunday_night["Challenge Type"] = "w01_sunday_night"
w01_sunday_night["Wildcard"] = False

w01_monday = df[df.Player.isin(["Russell Wilson", "Jerry Jeudy"])]
w01_monday["Display"] = get_player_display(w01_monday)
w01_monday["Challenge Type"] = "w01_monday"
w01_monday["Wildcard"] = False

w01_weekly = df[
    df.Player.isin(
        [
            "Justin Jefferson",
            "A.J. Brown",
            "Davante Adams",
            "Ja'Marr Chase",
            "Cooper Kupp",
            "Saquon Barkley",
            "Jonathan Taylor",
            "D'Andre Swift",
            "Nick Chubb",
            "Leonard Fournette",
            "Patrick Mahomes",
            "Matt Ryan",
            "Russell Wilson",
            "Joe Burrow",
            "Carson Wentz",
        ]
    )
    | (df.Set_Name == "Opening Acts")
    | df.Player.isin(w01_def[w01_def.sack >= 1].player_name.values)
]
w01_weekly["Display"] = get_player_display(w01_weekly)
w01_weekly["Challenge Type"] = "w01_weekly"
w01_weekly["Wildcard"] = ~w01_weekly.Player.isin(
    [
        "Justin Jefferson",
        "A.J. Brown",
        "Davante Adams",
        "Ja'Marr Chase",
        "Cooper Kupp",
        "Saquon Barkley",
        "Jonathan Taylor",
        "D'Andre Swift",
        "Nick Chubb",
        "Leonard Fournette",
        "Patrick Mahomes",
        "Matt Ryan",
        "Russell Wilson",
        "Joe Burrow",
        "Carson Wentz",
    ]
)


# --- Week 2
week2_df = weekly_df[weekly_df.week == 2]
week2_slate_df = week2_df[
    ~week2_df.team.isin(["LAC", "KC", "GB", "CHI", "MIN", "PHI", "BUF", "TEN"])
]
w02_def_pbp = pbp[
    (pbp.week == 2)
    & (
        (pbp.sack == 1)
        | (pbp.fumble == 1)
        | (pbp.interception == 1)
        | (pbp.solo_tackle == 1)
        | (pbp.tackled_for_loss == 1)
        | (pbp.assist_tackle == 1)
        | (pbp.tackle_with_assist == 1)
    )
][
    [
        "home_team",
        "away_team",
        "half_sack_1_player_id",
        "half_sack_2_player_id",
        "sack_player_id",
        "forced_fumble_player_1_player_id",
        "forced_fumble_player_2_player_id",
        "interception_player_id",
        "tackle_for_loss_1_player_id",
        "tackle_for_loss_2_player_id",
        "solo_tackle_1_player_id",
        "solo_tackle_2_player_id",
        "assist_tackle_1_player_id",
        "assist_tackle_2_player_id",
        "assist_tackle_3_player_id",
        "assist_tackle_4_player_id",
        "tackle_with_assist_1_player_id",
        "tackle_with_assist_2_player_id",
    ]
]
w02_def = get_def_df(w02_def_pbp, roster_df)

w02_thursday = df[
    (df.Player.isin(["Austin Ekeler", "Justin Herbert"]))
    | (
        df.Player.isin(
            [
                "Joey Bosa",
                "Khalil Mack",
                "J.C. Jackson",
                "Nick Niemann",
                "Nick Bolton",
                "Chris Jones",
                "Carlos Dunlap",
                "Tershawn Wharton",
            ]
        )
    )
    | ((df.Player.isin(["Patrick Mahomes II"])) & (df.Rarity > 0))
]
w02_thursday["Display"] = get_player_display(w02_thursday)
w02_thursday["Challenge Type"] = "w02_thursday"
w02_thursday["Wildcard"] = (w02_thursday.Player.isin(["Patrick Mahomes II"])) & (
    w02_thursday.Rarity > 0
)


w02_slate = df[
    (
        df.Player.isin(
            [
                "Tua Tagovailoa",
                "Lamar Jackson",
                "Tyreek Hill",
                "Amon-Ra St. Brown",
                "Mark Andrews",
                "Tyler Higbee",
                "Christian McCaffrey",
                "Nick Chubb",
            ]
        )
    )
    | ((df.Player.isin(get_top_n_players(week2_slate_df, 3))) & (df.Rarity > 0))
    | ((df.Player.isin(get_top_n_players(week2_slate_df, 5))) & (df.Rarity > 1))
]
w02_slate["Display"] = get_player_display(w02_slate)
w02_slate["Challenge Type"] = "w02_slate"
w02_slate["Wildcard"] = ~w02_slate.Player.isin(
    [
        "Tua Tagovailoa",
        "Lamar Jackson",
        "Tyreek Hill",
        "Amon-Ra St. Brown",
        "Mark Andrews",
        "Tyler Higbee",
        "Christian McCaffrey",
        "Nick Chubb",
    ]
)

w02_sunday_night = df[
    (
        df.Player.isin(
            [
                "AJ Dillon",
                "Aaron Jones",
                "David Montgomery",
            ]
        )
    )
    | (
        (df.Team.isin(["Green Bay Packers", "Chicago Bears"]))
        & (df.Set_Name == "Rivalries")
    )
]
w02_sunday_night["Display"] = get_player_display(w02_sunday_night)
w02_sunday_night["Challenge Type"] = "w02_sunday_night"
w02_sunday_night["Wildcard"] = ~w02_sunday_night.Player.isin(
    [
        "AJ Dillon",
        "Aaron Jones",
        "David Montgomery",
    ]
)

w02_monday = df[
    (
        df.Player.isin(
            [
                "Dallas Goedert",
                "Derrick Henry",
                "Josh Allen",
                "Minnesota Vikings",
                "Philadelphia Eagles",
                "Buffalo Bills",
                "Tennessee Titans",
            ]
        )
    )
    & (df.Position != "LB")  # not the LB Josh Allen
]
w02_monday["Display"] = get_player_display(w02_monday)
w02_monday["Challenge Type"] = "w02_monday"
w02_monday["Wildcard"] = False

w02_weekly = df[
    (
        (
            df.Player.isin(
                [
                    "Mac Jones",
                    "Najee Harris",
                    "Jaylen Waddle",
                    "Brock Wright",
                ]
            )
        )
        & (df.rookie_mint)
    )
    | (
        (
            df.Player.isin(
                get_top_n_players(week2_df, 2, by_recieving=True, by_total=False)
            )
        )
        & (df.Rarity > 0)
    )
    | (
        (
            df.Player.isin(
                get_top_n_players(week2_df, 5, by_recieving=True, by_total=False)
            )
        )
        & (df.Rarity > 1)
    )
    | (
        (df.Player.isin(w02_def[w02_def.tackle >= 3].player_name.values))
        & (df.rookie_mint)
    )
]
w02_weekly["Display"] = get_player_display(w02_weekly)
w02_weekly["Challenge Type"] = "w02_weekly"
w02_weekly["Wildcard"] = ~w02_weekly.Player.isin(
    [
        "Mac Jones",
        "Najee Harris",
        "Jaylen Waddle",
        "Brock Wright",
    ]
) & ~w02_weekly.Player.isin(w02_def[w02_def.tackle >= 3].player_name.values)
# (w02_thursday.Player.isin(["Patrick Mahomes II"])) & (
#     w02_thursday.Rarity > 0
# )


# --- Week 3
week3_df = weekly_df[weekly_df.week == 3]
week3_slate_df = week3_df[
    ~week3_df.team.isin(
        [
            "CLE",
            "PIT",
            "DEN",
            "SF",
            "DAL",
            "NYG",
        ]
    )
]
w03_def_pbp = pbp[
    (pbp.week == 3)
    & (
        (pbp.sack == 1)
        | (pbp.fumble == 1)
        | (pbp.interception == 1)
        | (pbp.solo_tackle == 1)
        | (pbp.tackled_for_loss == 1)
        | (pbp.assist_tackle == 1)
        | (pbp.tackle_with_assist == 1)
    )
][
    [
        "home_team",
        "away_team",
        "half_sack_1_player_id",
        "half_sack_2_player_id",
        "sack_player_id",
        "forced_fumble_player_1_player_id",
        "forced_fumble_player_2_player_id",
        "interception_player_id",
        "tackle_for_loss_1_player_id",
        "tackle_for_loss_2_player_id",
        "solo_tackle_1_player_id",
        "solo_tackle_2_player_id",
        "assist_tackle_1_player_id",
        "assist_tackle_2_player_id",
        "assist_tackle_3_player_id",
        "assist_tackle_4_player_id",
        "tackle_with_assist_1_player_id",
        "tackle_with_assist_2_player_id",
    ]
]
w03_def = get_def_df(w03_def_pbp, roster_df)
w03_sorted_carries = week3_df.sort_values(by="carries", ascending=False)
w03_sorted_targets = week3_df.sort_values(by="targets", ascending=False)
w03_sorted_completions = week3_df.sort_values(by="completions", ascending=False)

w03_thursday = df[
    df.Player.isin(
        [
            "Nick Chubb",
            "David Njoku",
            "Cameron Heyward",
        ]
    )
    | ((df["all_day_debut"] == 1) & (df.Team == "Cleveland Browns"))
]
w03_thursday["Display"] = get_player_display(w03_thursday)
w03_thursday["Challenge Type"] = "w03_thursday"
w03_thursday["Wildcard"] = ~w03_thursday.Player.isin(
    [
        "Nick Chubb",
        "David Njoku",
        "Cameron Heyward",
    ]
)

w03_slate = df[
    df.Player.isin(
        [
            "Josh Allen",
            "Jameis Winston",
            "Jalen Hurts",
            "Mac Jones",
            "Derek Carr",
            "Kyler Murray",
        ]
    )
    | (
        df.Player.isin(w03_def[w03_def.fumble >= 1].player_name.values)
        & (df.Position.isin(["DB", "DL", "LB"]))
        & (
            ~df.Team.isin(
                [
                    "Cleveland Browns",
                    "Dallas Cowboys",
                    "Denver Broncos",
                    "New York Giants",
                    "Pittsburgh Steelers",
                    "San Francisco 49ers",
                ]
            )
        )
    )
    | ((df.Position == "QB") & (df.Rarity > 1))
    | ((df.Position.isin(["DB", "DL", "LB"])) & (df.Rarity > 1))
]
w03_slate["Display"] = get_player_display(w03_slate)
w03_slate["Challenge Type"] = "w03_slate"
w03_slate["Wildcard"] = ~w03_slate.Player.isin(
    [
        "Josh Allen",
        "Jameis Winston",
        "Jalen Hurts",
        "Mac Jones",
        "Derek Carr",
        "Kyler Murray",
    ]
)

w03_sunday_night = df[
    df.Player.isin(
        [
            "Russell Wilson",
            "Courtland Sutton",
            "Javonte Williams",
            "Randy Gregory",
            "Bradley Chubb",
            "Nick Bosa",
        ]
    )
    | (
        (df.Team.isin(["Denver Broncos", "San Francisco 49ers"]))
        & (df.Series == "Historical")
    )
]
w03_sunday_night["Display"] = get_player_display(w03_sunday_night)
w03_sunday_night["Challenge Type"] = "w03_sunday_night"
w03_sunday_night["Wildcard"] = (w03_sunday_night.Series == "Historical") & (
    w03_sunday_night.Rarity > 0
)

w03_monday = df[
    df.Player.isin(
        [
            "CeeDee Lamb",
            "Ezekiel Elliott",
            "Saquon Barkley",
            "Dallas Cowboys",
        ]
    )
    | (
        (df.Team.isin(["Dallas Cowboys", "New York Giants"]))
        & (df.Player.isin(w03_def[w03_def.sack >= 1].player_name.values))
    )
    | (
        (df.Team.isin(["Dallas Cowboys", "New York Giants"]))
        & (df.Player.isin(week3_df[week3_df.carries > 0].player_display_name.values))
    )
    | ((df.Team.isin(["Dallas Cowboys", "New York Giants"])) & (df.Rarity > 1))
]
w03_monday["Display"] = get_player_display(w03_monday)
w03_monday["Challenge Type"] = "w03_monday"
w03_monday["Wildcard"] = w03_monday.Rarity > 1

w03_weekly = df[
    (
        (df["all_day_debut"] == 1) & (df.Team == "Jacksonville Jaguars")
        | (df.Player.isin(w03_sorted_carries.iloc[:5].player_display_name.values))
        | (df.Player.isin(w03_sorted_targets.iloc[:5].player_display_name.values))
        | (df.Player.isin(w03_sorted_completions.iloc[:5].player_display_name.values))
        | (df.Player.isin(w03_def[w03_def.tackle >= 10].player_name.values))
    )
]
w03_weekly["Display"] = get_player_display(w03_weekly)
w03_weekly["Challenge Type"] = "w03_weekly"
w03_weekly["Wildcard"] = False


# --- Week 4
week4_df = weekly_df[weekly_df.week == 4]
week4_slate_df = week4_df[~week4_df.team.isin(["CIN", "MIA", "KC", "TB", "SF", "LA"])]

w04_def_pbp = pbp[
    (pbp.week == 4)
    & (
        (pbp.sack == 1)
        | (pbp.fumble == 1)
        | (pbp.interception == 1)
        | (pbp.solo_tackle == 1)
        | (pbp.tackled_for_loss == 1)
        | (pbp.assist_tackle == 1)
        | (pbp.tackle_with_assist == 1)
    )
][
    [
        "home_team",
        "away_team",
        "half_sack_1_player_id",
        "half_sack_2_player_id",
        "sack_player_id",
        "forced_fumble_player_1_player_id",
        "forced_fumble_player_2_player_id",
        "interception_player_id",
        "tackle_for_loss_1_player_id",
        "tackle_for_loss_2_player_id",
        "solo_tackle_1_player_id",
        "solo_tackle_2_player_id",
        "assist_tackle_1_player_id",
        "assist_tackle_2_player_id",
        "assist_tackle_3_player_id",
        "assist_tackle_4_player_id",
        "tackle_with_assist_1_player_id",
        "tackle_with_assist_2_player_id",
    ]
]
w04_def = get_def_df(w04_def_pbp, roster_df)
w04_sorted_carries = week4_df[week4_df.carries > 0].sort_values(
    by="carries", ascending=False
)
w04_sorted_targets = week4_df[week4_df.targets > 0].sort_values(
    by="targets", ascending=False
)
w04_sorted_receptions = week4_df[week4_df.receptions > 0].sort_values(
    by="receptions", ascending=False
)
w04_sorted_attempts = week4_df[week4_df.attempts > 0].sort_values(
    by="attempts", ascending=False
)
w04_sorted_completions = week4_df[week4_df.completions > 0].sort_values(
    by="completions", ascending=False
)
w04_sorted_td_nopass = week4_df[
    (week4_df.rushing_tds > 0) | (week4_df.receiving_tds > 0)
]
w04_sorted_td_nopass["total_tds"] = (
    w04_sorted_td_nopass.rushing_tds + w04_sorted_td_nopass.receiving_tds
)
w04_sorted_td_nopass = w04_sorted_td_nopass.sort_values(by="total_tds", ascending=False)


w04_thursday = df[
    df.Player.isin(
        [
            "Joe Burrow",
            "Tyreek Hill",
            "Joe Mixon",
            "Bengals",
        ]
    )
    | (
        (
            df.Player.isin(
                w04_sorted_completions[
                    (w04_sorted_completions.team.isin(["MIA", "CIN"]))
                    & (w04_sorted_completions.position == "QB")
                ].player_display_name.values
            )
        )
        & (df.Rarity > 0)
    )
    | (
        (
            df.Player.isin(
                w04_sorted_receptions[
                    w04_sorted_receptions.team.isin(["MIA", "CIN"])
                ].player_display_name.values
            )
        )
        & (df.Rarity > 0)
    )
    | (
        (
            df.Player.isin(
                w04_sorted_attempts[
                    w04_sorted_attempts.team.isin(["MIA", "CIN"])
                ].player_display_name.values
            )
        )
        & (df.Rarity > 0)
    )
]
w04_thursday["Display"] = get_player_display(w04_thursday)
w04_thursday["Challenge Type"] = "w04_thursday"
w04_thursday["Wildcard"] = ~w04_thursday.Player.isin(
    [
        "Joe Burrow",
        "Tyreek Hill",
        "Joe Mixon",
        "Bengals",
    ]
)

w04_slate = df[
    df.Player.isin(
        [
            "Rashaad Penny",
            "Saquon Barkley",
            "Miles Sanders",
            "Nick Chubb",
            "Derrick Henry",
            "Josh Jacobs",
            "Aaron Jones",
        ]
    )
    | ((df.Team == "New York Giants") & (df.rookie_mint))
    | ((df.Team == "Seattle Seahawks") & (df.all_day_debut == 1))
    | (df.Rarity > 1)
]
w04_slate["Display"] = get_player_display(w04_slate)
w04_slate["Challenge Type"] = "w04_slate"
w04_slate["Wildcard"] = ~w04_slate.Player.isin(
    [
        "Rashaad Penny",
        "Saquon Barkley",
        "Miles Sanders",
        "Nick Chubb",
        "Derrick Henry",
        "Josh Jacobs",
        "Aaron Jones",
    ]
)

w04_sunday_night = df[
    ((df.Series == "Historical") & (df.Team == "Kansas City Chiefs"))
    | ((df.Rarity > 0) & (df.Team == "Tampa Bay Buccaneers"))
    | (
        df.Player.isin(
            w04_sorted_attempts[
                w04_sorted_attempts.team.isin(["TB", "KC"])
            ].player_display_name.values
        )
        & (df.all_day_debut == 1)
    )
]
w04_sunday_night["Display"] = get_player_display(w04_sunday_night)
w04_sunday_night["Challenge Type"] = "w04_sunday_night"
w04_sunday_night["Wildcard"] = ~(
    (
        (w04_sunday_night.Series == "Historical")
        & (w04_sunday_night.Team == "Kansas City Chiefs")
    )
    | (
        (w04_sunday_night.Rarity > 0)
        & (w04_sunday_night.Team == "Tampa Bay Buccaneers")
    )
)

w04_monday = df[
    df.Player.isin(
        [
            "Matthew Stafford",
            "Cooper Kupp",
        ]
    )
    | df.Player.isin(
        w04_sorted_td_nopass[
            (
                w04_sorted_td_nopass.team.isin(["SF", "LA"])
                & w04_sorted_td_nopass.position.isin(["RB", "WR", "TE"])
            )
        ].player_display_name.values
    )
    | ((df.Team == "San Francisco 49ers") & (df.all_day_debut == 1))
    | (
        (
            df.Team.isin(
                [
                    "San Francisco 49ers",
                    "Los Angeles Rams",
                ]
            )
        )
        & (df.Rarity > 1)
    )
]
w04_monday["Display"] = get_player_display(w04_monday)
w04_monday["Challenge Type"] = "w04_monday"
w04_monday["Wildcard"] = ~w04_monday.Player.isin(
    ["Matthew Stafford", "Cooper Kupp", "Deebo Samuel"]
)

w04_weekly = df[
    df.Player.isin(
        [
            "Jared Goff",
            "Austin Ekeler",
            "Mike Evans",
            "Jamal Agnew",
            "T.J. Hockenson",
            "Mo Alie-Cox",
        ]
    )
    | df.Player.isin(
        w04_def[(w04_def.sack >= 2) | (w04_def.interception >= 1)].player_name.values
    )
    | (df.Team.isin(["Seattle Seahawks", "Detroit Lions"]) & (df.Rarity > 0))
]
w04_weekly["Display"] = get_player_display(w04_weekly)
w04_weekly["Challenge Type"] = "w04_weekly"
w04_weekly["Wildcard"] = ~w04_weekly.Player.isin(
    [
        "Jared Goff",
        "Austin Ekeler",
        "Mike Evans",
        "Jamal Agnew",
        "T.J. Hockenson",
        "Mo Alie-Cox",
    ]
)

# #TODO: add other team?
w04_bills_ravens = df[df.Team.isin(["Baltimore Ravens", "Buffalo Bills"])]
w04_bills_ravens["Display"] = get_player_display(w04_bills_ravens)
w04_bills_ravens["Challenge Type"] = "w04_bills_ravens"
w04_bills_ravens["Wildcard"] = False
w04_bills_ravens["Winner"] = df.Team=="Baltimore Ravens"

w04_49ers_rams = df[df.Team.isin(["Los Angeles Rams", "San Francisco 49ers"])]
w04_49ers_rams["Display"] = get_player_display(w04_49ers_rams)
w04_49ers_rams["Challenge Type"] = "w04_49ers_rams"
w04_49ers_rams["Wildcard"] = False
w04_49ers_rams["Winner"] = df.Team=="San Francisco 49ers"

w04_stoppers_1 = df[
    (df.Position.isin(["DL", "DB", "K", "LB", "P"]) | (df.Play_Type == "Team Melt"))
    & df.Series.isin(["Series 1", "Historical"])
    & (df.Rarity > 0)
]
w04_stoppers_1["Display"] = get_player_display(w04_stoppers_1)
w04_stoppers_1["Challenge Type"] = "w04_stoppers_1"
w04_stoppers_1["Wildcard"] = False

w04_stoppers_2 = df[
    (df.Position.isin(["DL", "DB", "K", "LB", "P"]) | (df.Play_Type == "Team Melt"))
    & df.Series.isin(["Series 1", "Historical"])
    & (df.Rarity > 1)
]
w04_stoppers_2["Display"] = get_player_display(w04_stoppers_2)
w04_stoppers_2["Challenge Type"] = "w04_stoppers_2"
w04_stoppers_2["Wildcard"] = False

dfs = [
    w01_thursday,
    w01_slate,
    w01_sunday_night,
    w01_monday,
    w01_weekly,
    w02_thursday,
    w02_slate,
    w02_sunday_night,
    w02_monday,
    w02_weekly,
    w03_thursday,
    w03_slate,
    w03_sunday_night,
    w03_monday,
    w03_weekly,
    w04_thursday,
    w04_slate,
    w04_sunday_night,
    w04_monday,
    w04_weekly,
    w04_bills_ravens,
    w04_49ers_rams,
    w04_stoppers_1,
    w04_stoppers_2,
]

if __name__ == "__main__":
    for i, x in enumerate(dfs):
        x["Datetime"] = x["Datetime"].apply(lambda x: x.tz_localize("US/Eastern"))
        x["Index"] = x.index

        short_form = x["Challenge Type"].values[0]
        challenge_type = short_form[4:]
        print(f"#@# {short_form} full: {len(x)}")

        row = challenges.loc[challenges.short_form == short_form]
        week = row.Week.values[0]
        week_start, week_end = (
            pd.to_datetime(x).tz_localize("US/Eastern") for x in week_timings[week]
        )
        start, end = (
            pd.to_datetime(row[x].values[0]).tz_localize("US/Eastern")
            for x in ["Start Time (EDT)", "End Time (EDT)"]
        )

        x["during_week"] = (x.Datetime >= week_start) & (x.Datetime < week_end)
        x["during_challenge"] = (x.Datetime >= start) & (x.Datetime < end)
        x["post_challenge"] = x.Datetime >= end
        x["pre_challenge"] = x.Datetime < start
        try:
            game_start, game_end = game_timings[week][challenge_type]
            x["during_game"] = (x.Datetime >= game_start) & (x.Datetime < game_end)
        except KeyError:
            x["during_game"] = None

        x = x[x.during_week]
        print(f"#@# {short_form} during week: {len(x)}")
        print("-----")
        x.to_csv(
            f"data/challenges/{short_form}.csv.gz",
            index=False,
            compression="gzip",
        )
