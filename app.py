import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image
from scipy.stats import ttest_ind

from utils import *

st.set_page_config(page_title="NFL [Big Play] ALL DAY", page_icon="🏈", layout="wide")
alt.data_transformers.disable_max_rows()

st.title("🏈 NFL [Big Play] ALL DAY 🏈")
st.caption(
    """
Analyzing the biggest plays and most popular players featuring in NFL All Day Moments. 
"""
)


st.header("Methods")
with st.expander("Method details and data sources"):
    st.write(
        f"""
Data was queried using the [Flipside ShroomDK](https://sdk.flipsidecrypto.xyz/shroomdk) using [this query template](https://github.com/ltirrell/allday/blob/main/sql/sdk_allday.sql), acquiring all the sales data and metadata from the Flow tables.
Data is saved to a [GitHub repo](https://github.com/ltirrell/allday) ([data collection script](https://github.com/ltirrell/allday/blob/main/gather_data.py), [data directory](https://github.com/ltirrell/allday/blob/main/data)).
The script is currently manually ran at least once per week (to get new data for each NFL week).
Note that there may be some difference between this data (such as average sales price/number of sales) and what is listed at the NFL All Day Marketplace.

NFL stats information was obtained from [`nfl_data_py`](https://github.com/cooperdff/nfl_data_py).
See [here](https://github.com/nflverse/nflreadr/blob/bf1dc066c18b67823b9293d8edf252e3a58c3208/data-raw/dictionary_playerstats.csv) for a description of most metrics.
Season and play-by-play data, available since 1999, was used for determining whether of a player or play resulted in a score.

To determine whether a Moment NFT contains a video of a Touchdown score, the following information was used:
- **Description only (Moment TD)**: The Moment Description in the Flipside Data contains either of both of the case-insensitive words "TD" or "touchdown". This results in many false classifications, but is a good starting point without watching each video to determine the TD status.
- **Conservative (Moment TD)**: Play-by-play data was used to determine if the play in the Moment resulted in a TD. This is possible as the Quarter, clock time, and game information (season, week and teams) are available in the NFT metadata, and can be watch with what occurred at that game time. A few times (~15) did not match up, and these videos were watched to determine their TD status. All plays from seasons before 1999 would have a NaN/Null value for this determination, as play-by-play data is not available.
- **Conservative (In-game TD)**: Using NFT data regarding the player and the game, the seasonal NFL stats are checked to determine whether a player scored in that game. All plays from seasons before 1999 would have a NaN/Null value for this determination, as season data is not available.
- **Best Guess (Moment TD)**: This is the the same as **Conservative (Moment TD)** if it is not NaN, or else will match the **Description only (Moment TD)**. However, if **Conservative (In-game TD)** is False (meaning the seasonal stats data says the player didn't score that game), then this value will be False.
- **Best Guess: (In-game TD)**: This is the same as **Conservative (In-game TD)** if it is not NaN, or else will match the **Description only (Moment TD)**.

Game outcome was obtained using information from the NFT metadata-- the Home and Away team scores are available.
This is used to determine if the player's team won the game, or it resulted in a tie.

A [Bonferroni-corrected](https://en.wikipedia.org/wiki/Bonferroni_correction) [2-sided Welch's t-test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html) was used to determine whether TD scoring Moments had more sales or a higher price than those not scoring TDs.
The same was done for game winners/losers additionally.

A [Linear Mixed Effects Model](https://www.statsmodels.org/dev/examples/notebooks/generated/mixed_lm_example.html#) was used to determine which variables are predictive of a Moment's price, using the following model:
```
Price ~ Q("Scored Touchdown?") + Q("Game outcome") + Play_Type + Position + Rarity + (1|marketplace_id)
```
where 
- `Scored Touchdown` is whether the NFT contains a TD score based on the **Best Guess (Moment TD)** method
- `Game outcome` is whether the team won or lost
- `Play type` is one of the play types that could result in a TD (such as pass or rush)
- `Position` is the player's position
- `Rarity` is the Moment Tier, turned into a number from 0-3 (0 is COMMON, 3 is ULTIMATE)
- `marketplace_id` is the random effect, used to group the sales information based on this value. For example, [marketplace_id 1015](https://nflallday.com/listing/moment/1015) would group all of the sales for all of the 60 different Stephon Diggs Moment NFT IDs. NFT ID wasn't used, as all of them are the same (i.e. there are no features of an NFT with the same marketplace_id which vary by NFT ID).
Details can found in [this notebook](https://github.com/ltirrell/allday/blob/round3/what_drives_price.ipynb).

The [XGBoost Python Package](https://xgboost.readthedocs.io/en/stable/python/index.html) was used to determine feature importance using [this notebook](https://github.com/ltirrell/allday/blob/main/xgboost.ipynb).
Overall, the model explains about 69.2 percent of variance in the data (based on r^2 score); this isn't very accurate for prediction but is sufficient for determining which features most effect NFT Price.
"""
    )

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Challenges",
        "What Drives Price?",
        "Player Performance vs. Price",
        "Players or Play Types?",
    ]
)

with tab1:

    st.header("Challenges Overview")

    challenges = load_challenge_data()
    chart = (
        alt.Chart(challenges)
        .mark_bar()
        .encode(
            x=alt.X("yearmonthdatehoursminutes(Start Time (EDT)):T", title=None),
            x2=alt.X2("yearmonthdatehoursminutes(End Time (EDT)):T", title=None),
            y=alt.Y(
                "Name:N",
                sort=alt.EncodingSortField(
                    field="Index", op="count", order="ascending"
                ),
            ),
            color=alt.Color("Week:N"),
            tooltip=[
                alt.Tooltip("Name"),
                alt.Tooltip(
                    "yearmonthdatehoursminutes(Start Time (EDT))", title="Start Time"
                ),
                alt.Tooltip(
                    "yearmonthdatehoursminutes(End Time (EDT))", title="End Time"
                ),
                alt.Tooltip("Challenge Payout"),
                alt.Tooltip("Moments Needed"),
                alt.Tooltip("Completions", title="Users completing challenge"),
            ],
            href="URL",
        )
        .properties(height=500, width=1000)
    )

    st.altair_chart(chart, use_container_width=True)
    weekly_df, season_df = load_stats_data(2022)

    st.header("Driving downfield: price movement related to challenges")
    challenge = st.selectbox(
        "Choose a Challenge:",
        challenges.short_form.values,
        format_func=lambda x: f"Week {challenges[challenges.short_form == x].Week.values[0]} - {challenges[challenges.short_form == x].Name.values[0]}",  # #TODO: create function
        key="challenge_select",
    )
    challenge_type = challenge[4:]
    challenge_week = int(challenges[challenges.short_form == challenge].Week.values[0])
    challenge_name = challenges[challenges.short_form == challenge].Name.values[0]
    challenge_url = challenges[challenges.short_form == challenge].URL.values[0]
    challenge_description = challenges[challenges.short_form == challenge][
        "Challenge Text"
    ].values[0]
    challenge_start = pd.to_datetime(
        challenges[challenges.short_form == challenge]["Start Time (EDT)"].values[0]
    ).tz_localize("US/Eastern")
    challenge_end = pd.to_datetime(
        challenges[challenges.short_form == challenge]["End Time (EDT)"].values[0]
    ).tz_localize("US/Eastern")

    challenge_df, challenge_chart_df = load_challenge_player_data(challenge)

    date_dict = {
        "Datetime": [
            challenge_start,
            challenge_end,
        ],
        "Description": ["Challenge Start Time", "Challenge End Time"],
        "Color": ["gray", "gray"],
    }
    try:
        game_time = game_timings[challenge_week][challenge_type]
        date_dict["Datetime"].extend(list(game_time))
        date_dict["Description"].extend(
            ["Eligible Game(s) Start Time", "Eligible Game(s) End Time (approximate)"]
        )
        date_dict["Color"].extend(["red", "red"])
    except KeyError:
        pass
    time_df = pd.DataFrame(date_dict)

    c1, c2 = st.columns([1, 3])
    c1.subheader(f"[Week {challenge_week} - {challenge_name}]({challenge_url})")
    c1.write(challenge_description)

    if challenge in ["w04_bills_ravens", "w04_49ers_rams"]:  # #TODO
        shape_col = "Winner"
    else:
        shape_col = "Wildcard"

    combined = alt_challenge_chart(challenge_chart_df, time_df, shape_col)
    c2.altair_chart(combined, use_container_width=True)

    cols = st.columns(6)
    metric_data = {}
    for i, x in enumerate(
        [
            "pre_game_1d",
            "during_game",
            "post_game_1d",
            "during_challenge",
            "pre_challenge_1d",
            "post_challenge_1d",
            # "during_week",
            # "pre_challenge",
            # "post_challenge",
        ]
    ):
        c = cols[i]
        try:
            c.subheader(x.title().replace("_", " "))
            c.caption("Overall")
            metrics = get_challenge_summary(
                challenge_df,
                x,
            )
            for label, val in metrics:
                c.metric(label, val)
            c.caption("Per Unique Moment")
            metrics = get_challenge_summary(challenge_df, x, summary=False)
            for label, val in metrics:
                c.metric(label, val)
                metric_data[f"{x}-{label}"] = val
        except KeyError:
            pass

    st.subheader("Pregame warmup vs postgame cooldown")

    c1, c2, c3 = st.columns([1, 2, 2])
    metric = c1.radio("Choose a metric:", ["Price", "Count"], key="game_radio")
    grouped_game = (
        challenge_df.groupby(
            [
                "marketplace_id",
                "Player",
                "Position",
                "Team",
                "Moment_Tier",
                "site",
                "Display",
                "during_game",
            ]
        )
        .agg(Price=("Price", "mean"), Count=("Price", "count"))
        .reset_index()
    )
    grouped_challenge = (
        challenge_df.groupby(
            [
                "marketplace_id",
                "Player",
                "Position",
                "Team",
                "Moment_Tier",
                "site",
                "Display",
                "during_challenge",
            ]
        )
        .agg(Price=("Price", "mean"), Count=("Price", "count"))
        .reset_index()
    )
    game_chart = alt_challenge_game(grouped_game, "during_game", metric)
    challenge_chart = alt_challenge_game(grouped_challenge, "during_challenge", metric)

    c2.altair_chart(game_chart, use_container_width=True)
    c3.altair_chart(challenge_chart, use_container_width=True)

    results = get_challenge_ttests(challenge_df, use_cache=True)
    alpha = 0.05 / 4  # Bonferroni correction for 4 tests

    c1, c2, c3, c4 = st.columns(4)
    c1.subheader(
        "Are people  transacting more moments before games, or throughout games?"
    )
    k_price = "Before_Game_vs_During_Game_Price"
    v_price = results[k_price]
    sig = v_price < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['pre_game_1d-Median Price, per Moment']} vs {metric_data['during_game-Median Price, per Moment']}"
    c1.metric(k_price.replace("_", " "), f"{v_price:.3f}", delta_str)
    k_count = "Before_Game_vs_During_Game_Count"
    v_count = results[k_count]
    sig = v_count < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['pre_game_1d-Median Sales Count, per Moment']} vs {metric_data['during_game-Median Sales Count, per Moment']}"
    c1.metric(k_count.replace("_", " "), f"{v_count:.3f}", delta_str)

    c2.subheader(
        "Are people transacting more moments during games, or during challenges?"
    )
    k_price = "During_Game_vs_During_Challenge_Price"
    v_price = results[k_price]
    sig = v_price < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['during_game-Median Price, per Moment']} vs {metric_data['during_challenge-Median Price, per Moment']}"
    c2.metric(k_price.replace("_", " "), f"{v_price:.3f}", delta_str)
    k_count = "During_Game_vs_During_Challenge_Count"
    v_count = results[k_count]
    sig = v_count < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['during_game-Median Sales Count, per Moment']} vs {metric_data['during_challenge-Median Sales Count, per Moment']}"
    c2.metric(k_count.replace("_", " "), f"{v_count:.3f}", delta_str)

    c3.subheader(
        "Are people transacting more moments during challenges, or after challenges?"
    )
    k_price = "During_Challenge_vs_After_Challenge_Price"
    v_price = results[k_price]
    sig = v_price < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['during_challenge-Median Price, per Moment']} vs {metric_data['post_challenge_1d-Median Price, per Moment']}"
    c3.metric(k_price.replace("_", " "), f"{v_price:.3f}", delta_str)
    k_count = "During_Challenge_vs_After_Challenge_Count"
    v_count = results[k_count]
    sig = v_count < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['during_challenge-Median Sales Count, per Moment']} vs {metric_data['post_challenge_1d-Median Sales Count, per Moment']}"
    c3.metric(k_count.replace("_", " "), f"{v_count:.3f}", delta_str)

    c4.subheader(
        "Does floor price change after or during a challenge compared to before a challenge?"
    )
    k_price = "Before_Challenge_vs_After_Challenge_Floor"
    v_price = results[k_price]
    sig = v_price < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['pre_challenge_1d-Median Floor Price, per Moment']} vs {metric_data['post_challenge_1d-Median Floor Price, per Moment']}"
    c4.metric(k_price.replace("_", " "), f"{v_price:.3f}", delta_str)
    k_count = "Before_Challenge_vs_During_Challenge_Floor"
    v_count = results[k_count]
    sig = v_count < alpha
    delta_str = "+ Yes" if sig else "- No difference"
    delta_str += f": {metric_data['pre_challenge_1d-Median Floor Price, per Moment']} vs {metric_data['during_challenge-Median Floor Price, per Moment']}"
    c4.metric(k_count.replace("_", " "), f"{v_count:.3f}", delta_str)

    ###
    st.header("Hail Mary? Value proposition of completing challenges")

    if challenge_week == 4:
        st.write(
            "Data currently unavailable for Week 4, choose another challenge above"
        )
    else:
        df = load_score_data(
            f"2022 Week {challenge_week}", "Best Guess (Moment TD)", "All"
        )
        reward_df = load_challenge_reward()
        floor_price = df.Price.min()

        st.subheader("Reward breakdown")
        reward_weekly = reward_df[reward_df.Week == challenge_week]

        rare1 = reward_weekly.loc[
            reward_weekly.Reward_Star == 1, "Rare Proportion"
        ].values[0]
        rare2 = reward_weekly.loc[
            reward_weekly.Reward_Star == 2, "Rare Proportion"
        ].values[0]
        rare3 = reward_weekly.loc[
            reward_weekly.Reward_Star == 3, "Rare Proportion"
        ].values[0]
        rare4 = reward_weekly.loc[
            reward_weekly.Reward_Star == 4, "Rare Proportion"
        ].values[0]
        rare5 = reward_weekly.loc[
            reward_weekly.Reward_Star == 5, "Rare Proportion"
        ].values[0]
        legendary1 = reward_weekly.loc[
            reward_weekly.Reward_Star == 1, "Legendary Proportion"
        ].values[0]
        legendary2 = reward_weekly.loc[
            reward_weekly.Reward_Star == 2, "Legendary Proportion"
        ].values[0]
        legendary3 = reward_weekly.loc[
            reward_weekly.Reward_Star == 3, "Legendary Proportion"
        ].values[0]
        legendary4 = reward_weekly.loc[
            reward_weekly.Reward_Star == 4, "Legendary Proportion"
        ].values[0]
        legendary5 = reward_weekly.loc[
            reward_weekly.Reward_Star == 5, "Legendary Proportion"
        ].values[0]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.subheader("⭐ Packs")
        c2.subheader("⭐⭐ Packs")
        c3.subheader("⭐⭐⭐ Packs")
        c4.subheader("⭐⭐⭐⭐ Packs")
        c5.subheader("⭐⭐⭐⭐⭐ Packs")
        c1.metric(
            "Packs rewarded:",
            reward_weekly.loc[reward_weekly.Reward_Star == 1, "Packs_Total"].values[0],
        )
        c2.metric(
            "Packs rewarded:",
            reward_weekly.loc[reward_weekly.Reward_Star == 2, "Packs_Total"].values[0],
        )
        c3.metric(
            "Packs rewarded:",
            reward_weekly.loc[reward_weekly.Reward_Star == 3, "Packs_Total"].values[0],
        )
        c4.metric(
            "Packs rewarded:",
            reward_weekly.loc[reward_weekly.Reward_Star == 4, "Packs_Total"].values[0],
        )
        c5.metric(
            "Packs rewarded:",
            reward_weekly.loc[reward_weekly.Reward_Star == 5, "Packs_Total"].values[0],
        )

        c1.metric("Proportion Rare:", f"{rare1:.2%}")
        c2.metric("Proportion Rare:", f"{rare2:.2%}")
        c3.metric("Proportion Rare:", f"{rare3:.2%}")
        c4.metric("Proportion Rare:", f"{rare4:.2%}")
        c5.metric("Proportion Rare:", f"{rare5:.2%}")

        c1.metric("Proportion Legendary:", f"{legendary1:.2%}")
        c2.metric("Proportion Legendary:", f"{legendary2:.2%}")
        c3.metric("Proportion Legendary:", f"{legendary3:.2%}")
        c4.metric("Proportion Legendary:", f"{legendary4:.2%}")
        c5.metric("Proportion Legendary:", f"{legendary5:.2%}")

        c1.metric(
            "Moments Rewarded (1 Common):",
            f'{reward_weekly.loc[reward_weekly.Reward_Star==1, "Num Moments"].values[0]}',
        )
        c2.metric(
            "Moments Rewarded: (2 Common)",
            f'{reward_weekly.loc[reward_weekly.Reward_Star==2, "Num Moments"].values[0]}',
        )
        c3.metric(
            "Moments Rewarded (2 or 3 Common):",
            f'{reward_weekly.loc[reward_weekly.Reward_Star==3, "Num Moments"].values[0]}',
        )
        c4.metric(
            "Moments Rewarded (2 or 3 Common):",
            f'{reward_weekly.loc[reward_weekly.Reward_Star==4, "Num Moments"].values[0]}',
        )
        c5.metric(
            "Moments Rewarded (2 Common):",
            f'{reward_weekly.loc[reward_weekly.Reward_Star==5, "Num Moments"].values[0]}',
        )

        st.subheader("Sales Price Breakdown")
        c1, c2, c3 = st.columns(3)
        c1.metric(
            f"Floor price (average, Week {challenge_week})", f"${floor_price:.2f}"
        )
        c2.metric("Number of burns required for Playbook payouts", 5)
        c3.metric("Total cost for eligibilty", f"${floor_price * 5:.2f}")

        price_df = df.copy()
        price_df = price_df[price_df.Series != "Historical"]
        price_df["core"] = False
        price_df.loc[
            price_df.Set_Name.isin(
                [
                    "Base",
                    "Locked In",
                    "Iconic",
                ]
            ),
            "core",
        ] = True
        grouped_price_df = (
            price_df.groupby(["Moment_Tier", "Rarity", "core"])
            .Price.mean()
            .reset_index()
            .sort_values(by=["Rarity", "core"])[["Moment_Tier", "core", "Price"]]
        )
        c1.write("Average price by Tier and Set Type")
        c1.write(grouped_price_df)
        nstars = c2.selectbox(
            "Choose number of stars:",
            ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            key="star_select",
        )
        estimation_method = c2.radio(
            "Choose estimation method",
            ["Average Price", "Random sampling"],
            key="star_method",
        )

        star_dict = {
            "⭐": {"COMMON": 1, "RARE": 0, "LEGENDARY": 0},
            "⭐⭐": {"COMMON": 2 + 1, "RARE": 0, "LEGENDARY": 0},
            "⭐⭐⭐": {"COMMON": 2 + (1 - rare3) + 2 + 1, "RARE": rare3, "LEGENDARY": 0},
            "⭐⭐⭐⭐": {
                "COMMON": 2 + (1 - rare4) + 2 + (1 - rare3) + 2 + 1,
                "RARE": rare4 + rare3,
                "LEGENDARY": 0,
            },
            "⭐⭐⭐⭐⭐": {
                "COMMON": 2 + 2 + (1 - rare4) + 2 + (1 - rare3) + 2 + 1,
                "RARE": rare5 + rare4 + rare3,
                "LEGENDARY": legendary5,
            },
        }

        moments_needed = {  # #TODO: clean this up
            1: {
                "⭐": 2,
                "⭐⭐": 2 + 4,
                "⭐⭐⭐": 2 + 4 + 5,
                "⭐⭐⭐⭐": 2 + 4 + 5 + 5,
                "⭐⭐⭐⭐⭐": 2 + 4 + 5 + 5 + 8,
            },
            2: {
                "⭐": 4,
                "⭐⭐": 4 + 4,
                "⭐⭐⭐": 4 + 4 + 5,
                "⭐⭐⭐⭐": 4 + 4 + 5 + 5,
                "⭐⭐⭐⭐⭐": 4 + 4 + 5 + 5 + 8,
            },
            3: {
                "⭐": 3,
                "⭐⭐": 3 + 4,
                "⭐⭐⭐": 3 + 4 + 4,
                "⭐⭐⭐⭐": 3 + 4 + 4 + 5,
                "⭐⭐⭐⭐⭐": 3 + 4 + 4 + 5 + 8,
            },
        }

        total_reward = 0
        avg_price_dict = {
            "COMMON": grouped_price_df[
                (grouped_price_df["Moment_Tier"] == "COMMON")
                & (grouped_price_df["core"])
            ].Price.values[0],
            "RARE": grouped_price_df[
                (grouped_price_df["Moment_Tier"] == "RARE") & (grouped_price_df["core"])
            ].Price.values[0],
            "LEGENDARY": grouped_price_df[
                (grouped_price_df["Moment_Tier"] == "LEGENDARY")
                & (grouped_price_df["core"])
            ].Price.values[0],
        }
        total_cost = floor_price * moments_needed[challenge_week][nstars]

        if estimation_method == "Average Price":
            for k, v in star_dict[nstars].items():
                total_reward += avg_price_dict[k] * v
            c3.metric("Expected average Total cost (including burns)", f"${total_cost + (floor_price * 5):.2f}")
            c3.metric("Expected average reward value", f"${total_reward:.2f}", f"{total_reward - (total_cost + (floor_price * 5)):.2f} dollar return")

        else:
            c3.text("Not imlemented yet, try Average price")


with tab2:
    st.header("Two minute Drill: What drives Moment price?")
    st.write(
        f"""
    The chart below contains the whole 9 yards for investigating factors affecting price!
    Select the following:
    - Date Range: Sales data for All Time, since the current NFL season started, or specific weeks of this season
    - Play Types: we're mainly interested in whether a TD scored in the moment leads to a higher price, so choose a specific play type where scoring is possible, or look at all of them!
    - Method: Method used for determining whether the Moment encapsulates a TD score. See [Methods](#methods) for details.
    - Position Type: Divide results by Player's Positon, the Position Group, or Rarity level of the NFT
    - Game Metric: Color the points by whether the NFT contains a TD score, or whether the Player's team won the game. If Both are chosen, color is used for showing TD scoring and shape is used for showing game outcome.
    - Aggregation Metric: Plot the Average Sales Price of the NFT, or the Sales Count

    `Ctrl-Click` a point to open the the NFL All Day Marketplace page for an NFT in a new tab.
    *Note the log scale of the y-axis!*

    The sections below the chart show whether there is a price difference between TD scorers/non-scorers, and Game Winners/Losers.
    Explore for yourself to see the various differences!
        """
    )
    if st.checkbox("Load Section?", key="load_tab2"):
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        date_range = c1.selectbox(
            "Date range:",
            main_date_ranges,
            key="date_scores",
        )
        play_type = c2.selectbox(
            "Play Types",
            ["All"] + score_columns,
            key="play_types_scores",
        )
        how_scores = c3.selectbox(
            "Method",
            td_mapping.values(),
            key="how_scores",
        )
        position_type = c4.radio(
            "Position Type",
            position_type_dict.keys(),
            key="position_type",
        )
        metric = c5.radio(
            "Game Metric",
            ["Touchdown", "Game Outcome", "Both"],
            2,
            key="metric_scores",
        )
        agg_metric = c6.radio(
            "Aggregation Metric",
            ["Average Sales Price ($)", "Sales Count"],
            key="agg_metric_scores",
        )

        grouped = load_score_data(date_range, how_scores, play_type)
        select = alt.selection_single(on="mouseover")
        base = alt.Chart(grouped)
        chart = (
            base.mark_point(size=110, filled=True)
            .encode(
                x=alt.X(
                    "jitter:Q",
                    title=None,
                    axis=alt.Axis(values=[0], ticks=True, grid=False, labels=False),
                    scale=alt.Scale(),
                ),
                y=alt.Y(
                    "Price" if agg_metric == "Average Sales Price ($)" else "tx_id",
                    title=agg_metric,
                    scale=alt.Scale(
                        type="log",
                        zero=False,
                    ),
                ),
                color=alt.Color(
                    "Game Outcome" if metric == "Game Outcome" else "Scored Touchdown?",
                    scale=alt.Scale(
                        domain=["Win", "Loss", "Tie"]
                        if metric == "Game Outcome"
                        else [True, False, None],
                        range=["#1E88E5", "#D81B60", "#FFC107"],
                    ),
                ),
                shape=alt.value("circle")
                if metric != "Both"
                else alt.Shape(
                    "Game Outcome",
                    scale=alt.Scale(
                        domain=["Win", "Loss", "Tie"],
                        range=["circle", "triangle", "diamond"],
                    ),
                ),
                opacity=alt.condition(select, alt.value(1), alt.value(0.3)),
                tooltip=[
                    # alt.Tooltip("yearmonthdate(Date)", title="Date"),
                    alt.Tooltip("Player"),
                    alt.Tooltip("Position"),
                    alt.Tooltip("Team"),
                    alt.Tooltip("yearmonthdate(Moment_Date)", title="Game Date"),
                    alt.Tooltip("Moment_Tier", title="Rarity"),
                    alt.Tooltip("Total_Circulation", title="NFT Total Supply"),
                    # alt.Tooltip("Moment_Description", title="Description", band=1),
                    alt.Tooltip("Game Outcome"),
                    alt.Tooltip("Scored Touchdown?"),
                    alt.Tooltip("Price", title="Average Sales Price ($)", format=".2f"),
                    alt.Tooltip(
                        "tx_id",
                        title="Sales count",
                    ),
                ],
                href="site",
            )
            .transform_calculate(
                # Generate Gaussian jitter with a Box-Muller transform
                jitter="sqrt(-2*log(random()))*cos(2*PI*random())"
            )
            .interactive()
            .properties(height=800, width=125)
            .add_selection(select)
        )

        box = base.mark_boxplot(color="#004D40", outliers=False, size=25).encode(
            y=alt.Y(
                "Price" if agg_metric == "Average Sales Price ($)" else "tx_id",
                title=agg_metric,
            ),
        )
        combined_chart = (
            alt.layer(box, chart)
            .facet(
                column=alt.Column(
                    position_type_dict[position_type][0],
                    title=None,
                    header=alt.Header(
                        labelAngle=-90,
                        titleOrient="top",
                        labelOrient="bottom",
                        labelAlign="right",
                        labelPadding=3,
                    ),
                    sort=position_type_dict[position_type][1],
                ),
                title=f"Play Types: {play_type}",
            )
            .configure_facet(spacing=0)
        )

        st.altair_chart(combined_chart)
        st.write(
            f"""
        To statistically determine how price is related to these factors, we modeled the relationship between Price vs Play Type, Position of the Player, Rarity of the NFT, Game outcome (whether the NFT is for a winning team), and whether the NFT shows a TD score(see [Methods](#methods) for details). When looking at the entire dataset, the only factor which significantly affects price is **Rarity**.
        This is quite clear if viewing the `By Rarity Chart`; there is a clear separation of groups by the level.

        Other factors, such as TD scoring vs non TD scoring Moments, show some clear differences (see below), but these are not sufficient to fully explain the data and predict price.
            """
        )
        if position_type == "By Position":
            pos_subset = [
                x
                for x in positions
                if x in ["All"] + grouped.Position.unique().tolist()
            ]
            pos_column = position_type_dict[position_type][0]
        else:
            pos_subset = position_type_dict[position_type][1]
            pos_column = position_type_dict[position_type][0]

        ncols = len(pos_subset) if len(pos_subset) < 5 else 5

        st.subheader("Score for more?")
        st.write("**Are TD scores more sought after?**")
        st.write(
            f"""
        The price of TD scoring vs non-TD scoring Moments for each Position/Position Group/Rarity Level is shown. Any signifcant differences are marked. The percentage of TD scoring moments is shown in parentheses.
            """
        )
        cols = st.columns(ncols)
        tds_ttests = load_ttest(
            date_range,
            play_type,
            how_scores,
            agg_metric,
            position_type,
            how_scores,
            "TDs",
        )
        for i, x in enumerate(tds_ttests):
            position_info, comparison, sig = x
            cols[i % len(cols)].metric(
                position_info,
                comparison,
                sig,
            )

        st.subheader("Winner's circle")
        st.write("**Are game winning players traded more?**")
        st.write(
            f"""
        The price of Game Winners vs Game Losing Moments for each Position/Position Group/Rarity Level is shown. Any signifcant differences are marked. The percentage of Game Winners moments is shown in parentheses.
            """
        )
        cols = st.columns(ncols)
        winners_ttests = load_ttest(
            date_range,
            play_type,
            how_scores,
            agg_metric,
            position_type,
            "won_game",
            "Winners",
        )
        for i, x in enumerate(winners_ttests):
            position_info, comparison, sig = x
            cols[i % len(cols)].metric(
                position_info,
                comparison,
                sig,
            )

        st.subheader("Coach's challenge")
        st.write(
            "**If TDs are defined differently, does that lead to different results?**"
        )
        st.write(
            f"""
        For reference, a comparison between the `Best Guess` and `Description Only` methods for TD determination is shown in the box below.
            """
        )
        with st.expander("Comparison"):
            st.write(
                f"""
            There is generally a significant difference between the price of TD-scoring momemnts based on the method used. 
            The number in parentheses is the ratio of  Best Guess TD Moments to Description TD Moments (so `1.19 BG: Desc` means there are 1.19 times more Moments labeled as TD scoring using the Best guess method) 
                """
            )
            st.subheader("TD in moment")
            cols = st.columns(ncols)
            moment_best_guess_ttests = load_ttest(
                date_range,
                play_type,
                how_scores,
                agg_metric,
                position_type,
                ["Best Guess (Moment TD)", "Description only (Moment TD)"],
                "Best Guess Moment",
            )

            for i, x in enumerate(moment_best_guess_ttests):
                position_info, comparison, sig = x
                cols[i % len(cols)].metric(
                    position_info,
                    comparison,
                    sig,
                )

            st.subheader("TD in Game")
            cols = st.columns(ncols)
            game_best_guess_ttests = load_ttest(
                date_range,
                play_type,
                how_scores,
                agg_metric,
                position_type,
                ["Best Guess: (In-game TD)", "Description only (Moment TD)"],
                "Best Guess Game",
            )
            for i, x in enumerate(game_best_guess_ttests):
                position_info, comparison, sig = x
                cols[i % len(cols)].metric(
                    position_info,
                    comparison,
                    sig,
                )

with tab3:
    st.header("All Day Purchases based on recent Player performance")
    st.write(
        f"""
    Last we'll look at whether recent higher performing players have increased number of sales, or higher median or mean price.
    We'll use NFL stats for the players from a specific date range (the entire 2022 season, or from a specific week), and sort players by a given metric.
    Fantasy Points is used by default; while this isn't the best metric of a player, those who score high generally had big games.
    Players of all positions can be used, or you can select one of the available positions.
    Use the slider to select how many players to view.

    Top Players will show up in large circles in the chart below, and their NFT sales are compared with other players in the same timeframe.
    Explore all the different possible combinations!
    **Generally, the top players have increased sales and average price compared to the rest of the league**.

    `Ctrl-Click`ing a circle will open the video of the first Moment sold for that player on that day.
    """
    )
    if st.checkbox("Load Section?", key="load_tab3"):
        c1, c2, c3, c4, c5 = st.columns(5)
        date_range = c1.radio(
            "Date range:",
            stats_date_ranges,
            key="radio_stats",
        )
        position = c2.selectbox("Player Position", ["All", "QB", "RB", "WR", "TE"])
        metric = c3.selectbox(
            "Metric for top players:",
            [
                "fantasy_points_ppr",
                "passing_tds",
                "passing_yards",
                "receiving_tds",
                "receiving_yards",
                "rushing_tds",
                "rushing_yards",
            ],
            format_func=lambda x: x.replace("_", " ").title(),
            key="select_stats",
        )
        num_players = c4.slider("Number of top players:", 1, 32, 7, key="slider_stats")
        agg_metric = c5.radio(
            "Aggregation metric",
            ["median", "mean", "count"],
            format_func=lambda x: f"{x.title()} Price"
            if x != "count"
            else "Sales Count",
            key="radio_stats2",
        )

        weekly_df_2022, season_df_2022 = load_stats_data(years=2022)
        # #TODO: clean up date ranges
        if date_range == "2022 Full Season":
            stats_df = season_df_2022
        elif date_range == "2022 Week 1":
            stats_df = weekly_df_2022[weekly_df_2022.week == 1]
        elif date_range == "2022 Week 2":
            stats_df = weekly_df_2022[weekly_df_2022.week == 2]
        elif date_range == "2022 Week 3":
            stats_df = weekly_df_2022[weekly_df_2022.week == 3]
        elif date_range == "2022 Week 4":
            stats_df = weekly_df_2022[weekly_df_2022.week == 4]

        if position == "All":
            stats_df = stats_df.sort_values(by=metric, ascending=False).reset_index(
                drop=True
            )
        else:
            stats_df = (
                stats_df[stats_df["position"] == position]
                .sort_values(by=metric, ascending=False)
                .reset_index(drop=True)
            )
        df = load_player_data(date_range, agg_metric)

        top_players = stats_df.iloc[:num_players]
        player_display = top_players[
            ["player_display_name", "position", "team", metric]
        ].rename(
            columns={
                "player_display_name": "Player",
                "position": "Position",
                "team": "Team",
                metric: metric.replace("_", " ").title(),
            }
        )

        grouped = (
            df.groupby(["Date", "Player", "Position", "Team"])
            .Price.agg(agg_metric)
            .reset_index()
        )
        video_url = (
            df.groupby(["Date", "Player", "Position", "Team"])
            .NFLALLDAY_ASSETS_URL.first()
            .reset_index()
        )
        grouped = grouped.merge(video_url, on=["Date", "Player", "Position", "Team"])
        grouped["Date"] = pd.to_datetime(grouped["Date"])
        # grouped["Date"] = grouped.Date.dt.tz_localize("US/Pacific")
        # players = top_players[["player_display_name", "position"]]
        grouped["Top_Player"] = grouped.apply(
            lambda x: True
            if x.Player in top_players.player_display_name.values
            and x.Position
            in top_players.position.values  # HACK gets rid of the LB named Josh Allen
            else False,
            axis=1,
        )

        if position == "All":
            top_price = grouped[grouped.Top_Player]
            others = grouped[~grouped.Top_Player]
        else:
            top_price = grouped[
                (grouped["Position"] == position) & (grouped.Top_Player)
            ]
            others = grouped[(grouped["Position"] == position) & (~grouped.Top_Player)]

        if agg_metric == "count":
            ytitle = "Sales Count"
        elif agg_metric == "mean":
            ytitle = "Mean Sale Price ($)"
        elif agg_metric == "median":
            ytitle = "Median Sale Price ($)"

        c1, c2 = st.columns([2, 5])
        chart = (
            alt.Chart(grouped)
            .mark_circle()
            .encode(
                x=alt.X(
                    "jitter:Q",
                    title=None,
                    axis=alt.Axis(values=[0], ticks=True, grid=False, labels=False),
                    scale=alt.Scale(),
                ),
                y=alt.Y(
                    "Price",
                    title=ytitle,
                    scale=alt.Scale(type="log", zero=False, nice=False),
                ),
                color=alt.Color("Position"),
                column=alt.Column(
                    "yearmonthdate(Date)",
                    title=None,
                    header=alt.Header(
                        labelAngle=-90,
                        titleOrient="top",
                        labelOrient="bottom",
                        labelAlign="right",
                        labelPadding=3,
                    ),
                ),
                size=alt.Size("Top_Player", title="Top Player"),
                tooltip=[
                    alt.Tooltip("yearmonthdate(Date)", title="Date"),
                    alt.Tooltip(
                        "Player",
                    ),
                    alt.Tooltip(
                        "Position",
                    ),
                    alt.Tooltip(
                        "Team",
                    ),
                    alt.Tooltip(
                        "Price",
                        title=ytitle,
                        format=",.2f" if ytitle != "Sales Count" else ",",
                    ),
                ],
                href="NFLALLDAY_ASSETS_URL",
            )
            .transform_calculate(
                # Generate Gaussian jitter with a Box-Muller transform
                jitter="sqrt(-2*log(random()))*cos(2*PI*random())"
            )
            .configure_facet(spacing=0)
            .configure_view(stroke=None)
            .interactive()
            .properties(height=600, width=100)
        )

        c1.write(player_display)
        if agg_metric != "count":
            pval = ttest_ind(
                top_price.Price.values, others.Price.values, equal_var=False
            ).pvalue
            c1.metric(
                f"{ytitle}, Top Players (for selected positions)",
                f"{top_price.Price.agg(agg_metric):,.2f}",
            )
            c1.metric(
                f"{ytitle}, Other Players (for selected positions)",
                f"{others.Price.agg(agg_metric):,.2f}",
            )
        else:
            top_count = top_price.groupby("Player").Price.count()
            others_count = others.groupby("Player").Price.count()
            c1.metric(
                f"Average Sales Count, Top Players (for selected positions)",
                f"{top_count.mean():,.2f}",
            )
            c1.metric(
                f"Average Sales Count, Other Players (for selected positions)",
                f"{others_count.mean():,.2f}",
            )
            pval = ttest_ind(
                top_count.values, others_count.values, equal_var=False
            ).pvalue

        c1.metric(
            "Significant Difference?", f"{pval:.3f}", "+ Yes" if pval < 0.05 else "- No"
        )
        c2.altair_chart(chart)

        cols = st.columns(5)
        for i in list(range(num_players))[:5]:
            headshot_url = stats_df.iloc[i]["headshot_url"]
            try:  # don't want to error out if the image doesnt load
                image = load_headshot(headshot_url)
                cols[i].image(
                    image,
                    use_column_width="auto",
                )
            except:
                pass
            cols[i].metric(
                f"{player_display.iloc[i]['Player']} ({player_display.iloc[i]['Position']}) - {player_display.iloc[i]['Team']}",
                player_display.iloc[i][metric.replace("_", " ").title()],
                metric.replace("_", " ").title(),
            )

        with st.expander("Full Stats Infomation"):
            st.write(
                "All of the above stats information, obtained from [`nfl_data_py`](https://github.com/cooperdff/nfl_data_py). Uses the Date Range and Player Position from above. See [here](https://github.com/nflverse/nflreadr/blob/bf1dc066c18b67823b9293d8edf252e3a58c3208/data-raw/dictionary_playerstats.csv) for a description of most metrics."
            )
            st.write(stats_df)
            csv = convert_df(stats_df)

            st.download_button(
                "Press to Download",
                csv,
                f"nfl_stats_{date_range.replace(' ', '')}_Position-{position}.csv",
                "text/csv",
                key="download-csv",
            )

with tab4:
    st.header("Plays or Players?")
    st.write(
        f"""
    Is there a type of play that is more valuable, or do valuable players sell at higher prices regardless of play type?

    We'll break this down based on the date range of sales data, showing the top Players by mean sales price, as well as mean price for each Play Type. Select:
    - Date Range: A specific start date, or all available data
    - Moment Tier: The level of rarity-- All tiers, or Common, Rare, Legendary, or Ultimate (in order of increasing rarity)
    """
    )
    if st.checkbox("Load Section?", key="load_tab4"):
        date_range = st.radio(
            "Date range:",
            play_v_player_date_ranges,
            key="radio_summary",
            horizontal=True,
        )
        (
            play_type_price_data,
            play_type_tier_price_data,
            player_tier_price_data,
            topN_player_data,
        ) = load_play_v_player_data(date_range)

        tier = st.selectbox(
            "Choose the Moment Tier (the rarity level of the Moment NFT)",
            ["All Tiers", "COMMON", "RARE", "LEGENDARY", "ULTIMATE"],
            format_func=lambda x: x.title(),
            key="select_summary",
        )

        if tier == "All Tiers":
            player_chart = alt_mean_price(topN_player_data, "Player")
            play_type_chart = alt_mean_price(
                play_type_price_data, "Play_Type", y_title=None, y_labels=False
            )
        else:
            play_type_tier_subset = get_subset(
                play_type_tier_price_data, "Moment_Tier", tier
            )
            player_tier_subset = get_subset(player_tier_price_data, "Moment_Tier", tier)
            player_chart = alt_mean_price(player_tier_subset, "Player")
            play_type_chart = alt_mean_price(
                play_type_tier_subset, "Play_Type", y_title=None, y_labels=False
            )

        chart = alt.hconcat(player_chart, play_type_chart, spacing=10).resolve_scale(
            y="shared"
        )
        st.altair_chart(chart, use_container_width=True)

        with st.expander("Summary"):
            st.write(
                f"""
            **Note** that there have only been 2 sales of Ultimate NFTs, so we will not focus analysis on these.

            For `All Tiers`:
            - Pressure is the most valuable play type, regardless of Date range
            - Team-based moments have high mean sales price for before the start of Week 1, but after that it is generally mixed by position. 
            For `Common` moments:
            - QBs are generally the most popular position group for all Dates, with WR and RB also fairly popular (few in the top 40 for other position groups). Tom Brady has a particularly high mean price.
            - With the high number of QBs, it makes sense that Pass is the highest mean price for play types.
            For `Rare` and `Legendary` moments:
            - Similar trends are noted for Player positions and Play Type, though other QBs surpass Tom Brady at the top.
            - A Legendary 2-pt Attempt Play Type moment was sold for $5000, surpassing the average price of Pass and other play types.
            """
            )
        st.subheader("Don't hate the player")
        st.write(
            f"""
            Generally **Players are among the most important feature in determining Moment price**.
            That is, a moment from a very popular player (such as Tom Brady) would be expected to cost more than one from a less popular player (such as Lil'Jordan Humphrey).

            While this may seem obvious, it is backed up by some statistics. See the `Statisical Analysis` box below, and the [Methods](#methods) section for more details.
        """
        )

        with st.expander("Statistical Analysis"):
            st.write(
                f"""
            To analyze whether Players themselves or the Play Type captured in the Moment lead to more value, we used XGBoost to determine feature importance of our data.
            See [Methods](#methods) below for more details. Our model included 
            - `Player` name for the top 35 Players, with the remaining Players grouped into a `Player_Other` category
            - `Team` name for the top 6 Teams, with the remaining Teams grouped into a `Team_Other` category
            - `Position` name for the top 3 Postions, with the remaining Positions grouped into a `Postions_Other` category
            - `Play_Type` name for the top 4 Play_Types, with the remaining Play_Types grouped into a `Play_Type_Other` category
            - `Rarity`, coding the Moment Tier as an integer in increasing order of rarity
            - `Sales_Count`: the number of times a specific NFT is sold (e.g. if an NFT was sold 3 times, this number would be 3 for all rows of data)
            - `Resell Number`: for a specific transaction, the number of times that each specific NFT was resold (e.g. for the first ransaction of an NFT, this would be 0; if the same NFT was then purchased again, the second sale would have a value of 1)
            We used these features to determine the price of the NFT, determining which factors are best indicators of predicting the sale price of an NFT.

            We used 2 measures to assess feature importance: [gain](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.Booster.get_score) (how much a feature contributed to the model), and [SHAP](https://github.com/slundberg/shap) (an approach for explaining output of machine learning models) (see [here](https://stackoverflow.com/a/59007136) for a discussion of determining feature importance).

            Note: A feature is just a [measurable property of our data](https://en.wikipedia.org/wiki/Feature_(machine_learning)), such as whether the NFT is from a specific player. 
            """
            )
            c1, c2, c3 = st.columns(3)

            image = Image.open("images/gain_importance.png")
            baseheight = 700
            hpercent = baseheight / float(image.size[1])
            wsize = int((float(image.size[0]) * float(hpercent)))
            image = image.resize((wsize, baseheight), Image.Resampling.LANCZOS)

            c1.image(
                image,
                use_column_width="auto",
                caption="Figure 1: Gain for determination of Feature Importance",
            )
            image = Image.open("images/mean_shap.png")
            baseheight = 700
            hpercent = baseheight / float(image.size[1])
            wsize = int((float(image.size[0]) * float(hpercent)))
            image = image.resize((wsize, baseheight), Image.Resampling.LANCZOS)

            c2.image(
                image,
                use_column_width="auto",
                caption="Figure 2: Mean absolute SHAP values",
            )
            c3.write(
                f"""
            While the methods have some differences, both generally agree that **Player**, **Position** and **Rarity** are most importantant, while **Play_Type** is lower down on ranking.

            This makes sense, as average prices jump drastically as rarity increases, and as we saw above, certain specific players or position groups were among the highest average price.

            Figure 1:
            - Tom Brady, Patrick Mahomes, and several other QBs (as well as the position of QB itself) are highest on the list. That is, whether you are one of these players or not contributes the predicting the price of an NFT.
            - Rarity is the 4th ranked feature
            - The first `Play_type` is ranked around 25, showing that this has little relative effect in determining NFT price compared to Players

            Figure 2:
            - `Rarity`, followed by being a Player outside the top 35 or position outside the top 3 (not a QB, RB or Team-based Moment) explain the NFT the most
            - The number sales, and the resell number for NFTs also show value in determining price. Generally, people would like to resell at a profit (maybe investigated in a future analysis?) so more sales of a specific NFT may lead to a higher price overall.
            - Whether the Moment is of Tom Brady still has an important effect on explaining price.
            - `Play_Type_Interception` has the 8th highest mean SHAP value. Play Type appears higher in this method of explaining importance, but still below many Player-related categories
            """
            )
            st.write(
                f"""
            Some examples of interactions between features are shown below, described in clockwise from the top left:
            1. If an NFT has the feature `Player_Other` (red), our model would predict its price is lower for higher Rarity levels.
            2. The opposite effect is seen for `Position_QB`: for higher rarities, a QB NFT would be predicted to be hgiher.
            3. While more mixed, the the previous 2 charts, NFTs for `Position_Other` have higher prices at Rarity 1 (Rare), but lower prices at Rarity 2 (Legendary)
            4. `Play_Type_Interception` is similar to `Player_Other`: NFTs of this type are lower than those not of inteceptions at igher Rarity values.
            5. If an NFT is `Player_Other` (not a top-35 player by importance) and is a QB, its price is predicted to be lower.
            6. For `Play_Type Rush`, if a player is not `Position_Other` (so either QB, RB or Team), an NFT would be predicted to have lower value if the NFT shows a Rushing play.
            """
            )
            image = Image.open("images/interactions.png")
            st.image(
                image,
                use_column_width="auto",
                caption="Figure 3: Selection of interactions between features",
            )
