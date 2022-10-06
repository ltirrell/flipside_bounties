#!/usr/bin/env python3
import json
import pandas as pd

from utils import *


def get_score_data(score_data, date_range):
    # #TODO: clean up date ranges
    if date_range == "All Time":
        df = score_data
    elif date_range == "2022 Full Season":
        start =  week_timings[1][0]
        df = score_data[score_data.Date >= start]
    elif date_range == "2022 Week 1":
        start, end = week_timings[1]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    elif date_range == "2022 Week 2":
        start, end = week_timings[2]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    elif date_range == "2022 Week 3":
        start, end = week_timings[3]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    elif date_range == "2022 Week 4":
        start, end = week_timings[4]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    print(df.columns)
    grouped = df.groupby(["marketplace_id"]).agg(agg_dict).reset_index()
    grouped["Week"] = grouped.Week.astype(str)
    grouped["site"] = grouped.marketplace_id.apply(
        lambda x: f"https://nflallday.com/listing/moment/{x}"
    )

    grouped_all = grouped.copy()
    grouped_all["Position"] = "All"
    grouped_all["Position Group"] = "All"
    grouped = pd.concat([grouped, grouped_all]).reset_index(drop=True)
    del grouped_all

    return df, grouped


def get_player_data(main_data, date_range, agg_metric):
    # #TODO: clean up date ranges
    if date_range == "All Time":
        df = main_data
    elif date_range == "2022 Full Season":
        start =  week_timings[1][0]
        df = score_data[score_data.Date >= start]
    elif date_range == "2022 Week 1":
        start, end = week_timings[1]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    elif date_range == "2022 Week 2":
        start, end = week_timings[2]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    elif date_range == "2022 Week 3":
        start, end = week_timings[3]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]
    elif date_range == "2022 Week 4":
        start, end = week_timings[4]
        df = score_data[(score_data.Date >= start) & (score_data.Date < end)]

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
    grouped["Date"] = grouped.Date.dt.tz_localize("US/Pacific")

    return grouped


def get_play_v_player_data(main_data, date_range):
    # #TODO: clean up date ranges
    if date_range == "Since 2022 preseason":
        df = main_data[main_data.Date >= "2022-08-04"]
    elif date_range == "Since 2022 Week 1":
        start =  week_timings[1][0]
        df = main_data[main_data.Date >= start]
    elif date_range == "Since 2022 Week 2":
        start =  week_timings[2][0]
        df = main_data[main_data.Date >= start]
    elif date_range == "Since 2022 Week 3":
        start =  week_timings[3][0]
        df = main_data[main_data.Date >= start]
    elif date_range == "Since 2022 Week 4":
        start =  week_timings[4][0]
        df = main_data[main_data.Date >= start]
    else:
        df = main_data

    play_type_price_data = (
        df.groupby(
            [
                "Play_Type",
            ]
        )["Price"]
        .agg(["mean", "count"])
        .reset_index()
    )
    play_type_price_data["Position"] = "N/A"
    play_type_tier_price_data = (
        df.groupby(
            [
                "Play_Type",
                "Moment_Tier",
            ]
        )["Price"]
        .agg(["mean", "count"])
        .reset_index()
    )
    play_type_tier_price_data["Position"] = "N/A"

    player_price_data = (
        df.groupby(["Player", "Position"])["Price"].agg(["mean", "count"]).reset_index()
    )
    player_tier_price_data = (
        df.groupby(["Player", "Moment_Tier", "Position"])["Price"]
        .agg(["mean", "count"])
        .reset_index()
    )
    topN_player_data = (
        player_price_data.sort_values("mean", ascending=False)
        .reset_index(drop=True)
        .iloc[:n_players]
    )

    return (
        play_type_price_data,
        play_type_tier_price_data,
        player_tier_price_data,
        topN_player_data,
    )


if __name__ == "__main__":
    save_full = False
    main_data = load_allday_data(cols_to_keep)
    main_data["Position Group"] = main_data.Position.apply(get_position_group)

    score_data = main_data[main_data.Play_Type.isin(score_columns)].reset_index(
        drop=True
    )
    score_data = score_data.rename(columns=td_mapping)
    score_ttest_results = {}
    for date_range in main_date_ranges:
        date_str = date_range.replace(" ", "_")
        df, grouped = get_score_data(score_data, date_range)
        if save_full:
            df.to_csv(
                f"data/cache/score-{date_str}--df.csv.gz",
                compression="gzip",
                index=False,
            )
        grouped.to_csv(
            f"data/cache/{date_str}--grouped.csv",
            index=False,
        )
        for play_type in ["All"] + score_columns:
            for how_scores in td_mapping.values():
                # substr = (
                #     f"{date_range}--{play_type}--{how_scores}".replace(" ", "_")
                #     .replace(")", "")
                #     .replace("(", "")
                # )
                # print(f"#@# Working on: {substr}")

                df["Scored Touchdown?"] = df[how_scores]
                if play_type != "All":
                    df = df[df.Play_Type == play_type]
                for agg_metric in ["Average Sales Price ($)", "Sales Count"]:
                    for position_type in position_type_dict.keys():
                        if position_type == "By Position":
                            pos_subset = [
                                x
                                for x in positions
                                if x in ["All"] + df.Position.unique().tolist()
                            ]
                            pos_column = position_type_dict[position_type][0]
                        else:
                            pos_subset = position_type_dict[position_type][1]
                            pos_column = position_type_dict[position_type][0]
                        for metric, short_form in [
                            (
                                how_scores,
                                "TDs",
                            ),
                            (
                                "won_game",
                                "Winners",
                            ),
                            (
                                [
                                    "Best Guess (Moment TD)",
                                    "Description only (Moment TD)",
                                ],
                                "Best Guess Moment",
                            ),
                            (
                                [
                                    "Best Guess: (In-game TD)",
                                    "Description only (Moment TD)",
                                ],
                                "Best Guess Game",
                            ),
                        ]:
                            if agg_metric == "Sales Count" and type(metric) == str:
                                ttest_df = grouped
                                agg_column = "tx_id"
                            else:
                                ttest_df = df
                                agg_column = "Price"
                            ttest_res = get_ttests(
                                ttest_df,
                                metric,
                                pos_subset,
                                short_form,
                                pos_column,
                                agg_column,
                            )
                            substr = (
                                f"{date_range}--{play_type}--{how_scores}--{agg_metric}--{position_type}--{metric}--{short_form}".replace(
                                    " ", "_"
                                )
                                .replace(")", "")
                                .replace("(", "")
                            )
                            print(f"#@# Working on: {substr}")
                            score_ttest_results[substr] = ttest_res

    with open("data/cache/score_ttest_results.json", "w") as f:
        json.dump(score_ttest_results, f)

    for date_range in main_date_ranges:
        date_str = date_range.replace(" ", "_")
        for agg_metric in ["median", "mean", "count"]:
            grouped = get_player_data(main_data, date_range, agg_metric)
            grouped.to_csv(
                f"data/cache/player-{date_str}-{agg_metric}--grouped.csv",
                index=False,
            )

    for date_range in play_v_player_date_ranges:
        date_str = date_range.replace(" ", "_")
        (
            play_type_price_data,
            play_type_tier_price_data,
            player_tier_price_data,
            topN_player_data,
        ) = get_play_v_player_data(main_data, date_range)
        play_type_price_data.to_csv(
            f"data/cache/play_v_player-play_type-{date_str}--grouped.csv",
            index=False,
        )
        play_type_tier_price_data.to_csv(
            f"data/cache/play_v_player-play_type_tier-{date_str}--grouped.csv",
            index=False,
        )
        player_tier_price_data.to_csv(
            f"data/cache/play_v_player-player_tier-{date_str}--grouped.csv",
            index=False,
        )
        topN_player_data.to_csv(
            f"data/cache/play_v_player-topN_player-{date_str}--grouped.csv",
            index=False,
        )
