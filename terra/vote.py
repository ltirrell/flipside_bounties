# # Votes, Votes, Votes
# > On average, how much voting power (in Luna) was used to vote 'YES' for governance proposals? Out of this, how much Luna comes from validators vs regular wallets?

from typing import List
import altair as alt
import numpy as np
import pandas as pd
import requests
import streamlit as st

LCD = "https://lcd.terra.dev"

st.title("Votes, Votes, Votes")
st.caption(
    "On average, how much voting power (in Luna) was used to vote 'YES' for governance proposals? Out of this, how much Luna comes from validators vs regular wallets?"
)


@st.cache(ttl=7200, allow_output_mutation=True)
def load_data():
    q = "20f89eaa-e7f5-42b9-834f-45027923775a"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)
    df = df.sort_values(by=["PROPOSAL_ID", "DATETIME"])
    df = df.drop_duplicates(["VOTER", "PROPOSAL_ID"], keep="last")

    return df


def load_proposal_data():
    proposals_url = LCD + "/cosmos/gov/v1beta1/proposals"
    proposals = []
    r = requests.get(proposals_url).json()
    next_key = r["pagination"]["next_key"]
    while next_key is not None:
        proposals.extend(r["proposals"])

        next_key = r["pagination"]["next_key"]
        payload = {"pagination.key": next_key}
        r = requests.get(proposals_url, params=payload).json()

    proposal_df = pd.DataFrame.from_dict(parse_proposals(proposals))
    proposal_df["submit_time"] = pd.to_datetime(
        proposal_df["submit_time"], errors="coerce"
    )
    proposal_df["voting_start_time"] = pd.to_datetime(
        proposal_df["voting_start_time"], errors="coerce"
    )
    proposal_df["voting_end_time"] = pd.to_datetime(
        proposal_df["voting_end_time"], errors="coerce"
    )
    proposal_df["total_votes"] = (
        proposal_df["Yes"]
        + proposal_df["No"]
        + proposal_df["NoWithVeto"]
        + proposal_df["Abstain"]
    )
    proposal_df["proportion_yes"] = proposal_df["Yes"] / proposal_df["total_votes"]

    long_proposal_df = proposal_df.melt(
        value_vars=[
            "Yes",
            "Abstain",
            "No",
            "NoWithVeto",
        ],
        id_vars=[
            "proposal_id",
            "title",
            "description",
            "type",
            "submit_time",
            "voting_start_time",
            "voting_end_time",
            "status",
            "total_votes",
            "proportion_yes",
        ],
        var_name="option",
        value_name="voting_power",
    )

    long_non_val_df = (
        df.groupby(["OPTION", "PROPOSAL_ID"])
        .VOTING_POWER.agg(["sum", "count", "mean"])
        .reset_index()
        .rename(
            columns={
                "sum": "non_val_voting_power",
                "mean": "non_val_voting_power_avg",
                "count": "non_val_voters",
                "OPTION": "option",
                "PROPOSAL_ID": "proposal_id",
            }
        )
    )

    merged_df = (
        long_proposal_df.merge(
            long_non_val_df, on=["option", "proposal_id"], how="left"
        )
        .sort_values(["proposal_id", "option"])
        .reset_index(drop=True)
    )
    merged_df = merged_df.replace(np.nan, 0)
    merged_df["val_voting_power"] = (
        merged_df["voting_power"] - merged_df["non_val_voting_power"]
    )
    merged_df["non_val_proportion"] = (
        merged_df["non_val_voting_power"] / merged_df["voting_power"]
    )

    return proposal_df, merged_df


def convert_udenom(amount: str) -> float:
    return float(amount) / 1_000_000


def parse_proposals(p: List[dict]) -> List[dict]:
    """Get the useful content related to proposals from JSON pulled from the Terra LCD

    Parameters
    ----------
    p : List[dict]
        List containing dicts, each dict has relecant information on the proposal

    Returns
    -------
    List[dict]
        List that can be loaded cleanly into a pandas dataframe
    """
    proposal_info = []
    for d in p:
        info = {
            "proposal_id": int(d["proposal_id"]),
            "title": d["content"]["title"],
            "description": d["content"]["description"],
            "type": d["content"]["@type"].split(".")[-1],
            "status": d["status"],
            "Yes": convert_udenom(d["final_tally_result"]["yes"]),
            "Abstain": convert_udenom(d["final_tally_result"]["abstain"]),
            "No": convert_udenom(d["final_tally_result"]["no"]),
            "NoWithVeto": convert_udenom(d["final_tally_result"]["no_with_veto"]),
            "submit_time": d["submit_time"],
            "deposit_end_time": d["deposit_end_time"],
            "voting_start_time": d["voting_start_time"],
            "voting_end_time": d["voting_end_time"],
        }
        try:
            total_deposit_luna = convert_udenom(d["total_deposit"][0]["amount"])
        except IndexError:
            total_deposit_luna = 0
        info["total_deposit_luna"] = total_deposit_luna
        proposal_info.append(info)
    return proposal_info


def get_proposal_info(df, proposal_status):
    if proposal_status == "All":
        sub_df = df
    elif proposal_status == "Completed":
        sub_df = df[
            df["status"].isin(["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"])
        ]
    else:
        sub_df = df[df["status"] == proposal_status]
    vals = sub_df[["proposal_id", "title"]].values
    titles = ["All"] + [f"{x[0]}: {x[1]}" for x in vals]

    return titles, sub_df.reset_index(drop=True)


df = load_data()
proposal_df, merged_df = load_proposal_data()
open_proposals = proposal_df[proposal_df.status == "PROPOSAL_STATUS_VOTING_PERIOD"]


st.header("LUNA governance overview")
st.write(
    """
Terra users delegate their LUNA to a validator to particpate in the security of the blockchain.
By doing so, users get the right to vote on proposals, in addition to staking yield.

Users have 2 options to participate in this governance process:
- Vote on open polls using Terra Station
- Do nothing. The user's staked LUNA will vote the same way as the validator it is delegated to.

For example, Do stakes 100 LUNA to Terrafic Validator. For proposal 420, Terrafic Validator votes "Yes".
If Do does nothing, his 100 LUNA will count towards the "Yes" vote.
However, if Do doesn't agree with this decision, he can vote "No" on this proposal with his 100 LUNA, and it wouldn't count as part of the validator's vote.

Currently open governance proposals are can be found at the link below.
Fulfill you civic duty and vote!

---
"""
)

col1, col2 = st.columns(2)
col1.metric("Open Governance Proposals", len(open_proposals))
col2.write(
    "[Vote here!](https://station.terra.money/gov#PROPOSAL_STATUS_VOTING_PERIOD)"
)

st.subheader("Voting breakdown")
st.write(
    """
Results of past governance votes are shown below, with both the vote perentages and the amount of LUNA used for each voting option.
"""
)
completed_df = merged_df[
    merged_df["status"].isin(["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"])
]

chart_percentage = (
    alt.Chart(completed_df)
    .mark_bar()
    .encode(
        alt.X("proposal_id:N", axis=None, title="Proposals"),
        alt.Y("voting_power", stack="normalize", title="Vote Percentage"),
        alt.Color(
            "option",
            sort=["Yes", "No", "NoWithVeto", "Abstain"],
            legend=alt.Legend(orient="bottom"),
            title="Voting Option",
        ),
        tooltip=[
            alt.Tooltip("proposal_id", title="Proposal ID"),
            alt.Tooltip("title", title="Proposal Title"),
            alt.Tooltip("option", title="Option"),
            alt.Tooltip("voting_power", title="Voting Power, LUNA", format=",.0f"),
            alt.Tooltip("status", title="Status"),
            alt.Tooltip("voting_end_time", title="Vote end date"),
        ],
    )
    .properties(width=800)
)
chart_values = (
    alt.Chart(completed_df)
    .mark_bar()
    .encode(
        alt.X("proposal_id:N", axis=None, title="Proposals"),
        alt.Y("voting_power", title="Voting Power (LUNA)"),
        alt.Color("option", sort=["Yes", "No", "NoWithVeto", "Abstain"]),
        tooltip=[
            alt.Tooltip("proposal_id", title="Proposal ID"),
            alt.Tooltip("title", title="Proposal Title"),
            alt.Tooltip("option", title="Option"),
            alt.Tooltip("voting_power", title="Voting Power, LUNA", format=",.0f"),
            alt.Tooltip("status", title="Status"),
            alt.Tooltip("voting_end_time", title="Vote end date"),
        ],
    )
    .properties(width=800)
)
st.altair_chart(chart_percentage & chart_values, use_container_width=True)


total_proposals = len(proposal_df.proposal_id.unique())
completed_votes = len(
    proposal_df[
        proposal_df.status.isin(["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"])
    ]
)
no_vote = len(proposal_df[proposal_df.status == "PROPOSAL_STATUS_DEPOSIT_PERIOD"])
open_proposals = len(proposal_df[proposal_df.status == "PROPOSAL_STATUS_VOTING_PERIOD"])
rejected_proposals = len(proposal_df[proposal_df.status == "PROPOSAL_STATUS_REJECTED"])
passed_proposals = len(proposal_df[proposal_df.status == "PROPOSAL_STATUS_PASSED"])


st.write(
    "To make a governance proposal, a minimum deposit threshold of 50 LUNA needs to be met. Without this, the proposal will not be voted upon. Additionally, a quorum of votes need to be participate in the proposal in order for a vote to pass."
)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Proposals", total_proposals)
col2.metric("Completed Votes", completed_votes)
col3.metric("Proposals without votes", no_vote)
col4.metric("Open Proposals", open_proposals)


st.write(
    f"""
Here is the breakdown of proposals that passed governance.
Of the {total_proposals} that recieved the minimum deposit and were sent to a vote, {passed_proposals} passed and {rejected_proposals} failed, for a {passed_proposals/completed_votes:.1%} success rate.
"""
)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Passed Proposals", passed_proposals)
col2.metric("Passed Percentage", f"{passed_proposals/completed_votes:.1%}")
col3.metric("Rejected Proposals", rejected_proposals)
col4.metric("Rejected Percentage", f"{rejected_proposals/completed_votes:.1%}")


st.subheader("Yes we can!")
yes_summary = proposal_df[
    proposal_df.status.isin(["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"])
][["Yes", "status", "proportion_yes", "total_votes", "proposal_id"]]
st.write(
    f"""Next, we'll look exclusively at votes who voted "Yes" on the {completed_votes} completed proposals.
- Overall, a voting power of {yes_summary.Yes.sum():,.0f} LUNA voted 'Yes' in governance proposals out of a total of {yes_summary.total_votes.sum():,.0f} voted LUNA.
    - For all votes: {yes_summary.Yes.mean():,.1f} ± {yes_summary.Yes.std()/np.sqrt(len(yes_summary)):,.1f} LUNA per vote
    - For votes that passed: {yes_summary[yes_summary.status=='PROPOSAL_STATUS_PASSED'].Yes.mean():,.1f} ± {yes_summary[yes_summary.status=='PROPOSAL_STATUS_PASSED'].Yes.std()/np.sqrt(len(yes_summary[yes_summary.status=='PROPOSAL_STATUS_PASSED'])):,.1f} LUNA per vote
    - For votes that were rejected: {yes_summary[yes_summary.status=='PROPOSAL_STATUS_REJECTED'].Yes.mean():,.1f} ± {yes_summary[yes_summary.status=='PROPOSAL_STATUS_REJECTED'].Yes.std()/np.sqrt(len(yes_summary[yes_summary.status=='PROPOSAL_STATUS_REJECTED'])):,.1f} LUNA per vote
- An average of {yes_summary.proportion_yes.mean():.1%} ± {yes_summary.proportion_yes.std()/np.sqrt(len(yes_summary)):.1%} voted Yes for proposals
    - For votes that passed: {yes_summary[yes_summary.status=='PROPOSAL_STATUS_PASSED'].proportion_yes.mean():.1%} ± {yes_summary[yes_summary.status=='PROPOSAL_STATUS_PASSED'].proportion_yes.std()/np.sqrt(len(yes_summary[yes_summary.status=='PROPOSAL_STATUS_PASSED'])):.1%}
    - For votes that were rejected: {yes_summary[yes_summary.status=='PROPOSAL_STATUS_REJECTED'].proportion_yes.mean():.1%} ± {yes_summary[yes_summary.status=='PROPOSAL_STATUS_REJECTED'].proportion_yes.std()/np.sqrt(len(yes_summary[yes_summary.status=='PROPOSAL_STATUS_REJECTED'])):.1%}
There is quite a clear slant for voting Yes on proposals.
Also, proposals are generally passed or rejected by a wide margin: nearly 90% votes for passed proposals are Yes on average.
For rejected proposals, about 69% of votes are No on average. This may be skewed lower, as some rejected proposals (such as proposal 5) had low percentage of No votes but did not meet Quorum so were rejected
"""
)
yes_df = (
    completed_df[completed_df.option == "Yes"]
    .rename(
        columns={"voting_power": "Validator", "non_val_voting_power": "Regular wallet"}
    )
    .melt(
        id_vars=[
            "proposal_id",
            "title",
            "voting_end_time",
            "submit_time",
            "status",
            "option",
            "total_votes",
        ],
        value_vars=["Validator", "Regular wallet"],
        var_name="Voter Type",
        value_name="Voting Power",
    )
).sort_values(by=["Voter Type", "proposal_id"])
yes_df["proportion_yes"] = yes_df["Voting Power"] / yes_df.total_votes

# TODO: work on this later?
# non_val_voting_power = completed_df.groupby("proposal_id").non_val_voting_power.sum()
# val_voting_power = completed_df.groupby("proposal_id").val_voting_power.sum()
# total_votes_category = pd.concat([non_val_voting_power, val_voting_power]).reset_index(drop=True)

# yes_df["total_votes_category"] = total_votes_category
# yes_df["proportion_yes_category"] = yes_df["Voting Power"] / yes_df.total_votes_category

st.write(
    """Looking at histograms of this data (note that bars are not stacked), we see overall low Voting Power voting Yes for rejected proposals.
For passed proposals, the Voting power amount is more spread across the range of values though has a much higher minimum value.

The proportion voting Yes shows a high count of records for passed proposals.
There are 6 rejected proposals with a >50% proportion Yes, suggested that these did not meet quorum and were thus rejected.
    """
)
chart_voting_power = (
    alt.Chart(
        yes_df.groupby(["proposal_id", "status"])["Voting Power"].sum().reset_index()
    )
    .mark_bar(binSpacing=0, opacity=0.65)
    .encode(
        alt.X("Voting Power", bin=alt.Bin(maxbins=25)),
        alt.Y(
            "count()",
            stack=None,
        ),
        alt.Order(
            "count(Voting Power)",
            sort="descending",
        ),
        alt.Color(
            "status",
        ),
        tooltip=[
            alt.Tooltip("status", title="Vote result"),
            alt.Tooltip(
                "average(Voting Power)",
                title="Average Voting Power in bin, LUNA",
                format=",.0f",
            ),
            alt.Tooltip("count(Voting Power)", title="Proposals in bin", format=",.0f"),
        ],
    )
    .properties(width=800)
).interactive()

chart_proportion = (
    alt.Chart(
        yes_df.groupby(["proposal_id", "status"])["proportion_yes"].mean().reset_index()
    )
    .mark_bar(binSpacing=0, opacity=0.65)
    .encode(
        alt.X(
            "proportion_yes",
            bin=alt.Bin(maxbins=25),
            title="Proportion voting Yes (binned)",
        ),
        alt.Y(
            "count()",
            stack=None,
        ),
        alt.Order(
            "count(proportion_yes)",
            sort="descending",
        ),
        alt.Color("status", legend=alt.Legend(orient="bottom", title="Vote results")),
        tooltip=[
            alt.Tooltip("status", title="Vote result"),
            alt.Tooltip(
                "average(proportion_yes)",
                title="Average Proportion voting Yes in bin",
                format=",.2%",
            ),
            alt.Tooltip(
                "count(proportion_yes)", title="Proposals in bin", format=",.0f"
            ),
        ],
    )
    .properties(width=800)
).interactive()
st.altair_chart(chart_voting_power & chart_proportion, use_container_width=True)


st.write(
    f"""
The vast majority of voting power comes from Validators. For regular wallets:
- A voting power of {yes_df[yes_df["Voter Type"]=="Regular wallet"]["Voting Power"].sum():,.0f} LUNA voted 'Yes' in governance proposals out of a total of {yes_df[yes_df["Voter Type"]=="Regular wallet"].total_votes.sum():,.0f} voted LUNA came from regular wallets.
    - For all votes: {yes_df[yes_df["Voter Type"]=="Regular wallet"]["Voting Power"].mean():,.1f} ± {yes_df[yes_df["Voter Type"]=="Regular wallet"]["Voting Power"].std()/np.sqrt(len(yes_df[yes_df["Voter Type"]=="Regular wallet"])):,.1f} LUNA per vote
    - For votes that passed: {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_PASSED']["Voting Power"].mean():,.1f} ± {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_PASSED']["Voting Power"].std()/np.sqrt(len(yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_PASSED'])):,.1f} LUNA per vote
    - For votes that were rejected: {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_REJECTED']["Voting Power"].mean():,.1f} ± {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_REJECTED']["Voting Power"].std()/np.sqrt(len(yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_REJECTED'])):,.1f} LUNA per vote
- An average of {yes_df[yes_df["Voter Type"]=="Regular wallet"].proportion_yes.mean():.1%} ± {yes_df[yes_df["Voter Type"]=="Regular wallet"].proportion_yes.std()/np.sqrt(len(yes_df[yes_df["Voter Type"]=="Regular wallet"])):.1%} of Yes votes came from regular wallets.
    - For votes that passed: {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_PASSED'].proportion_yes.mean():.1%} ± {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_PASSED'].proportion_yes.std()/np.sqrt(len(yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_PASSED'])):.1%}
    - For votes that were rejected: {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_REJECTED'].proportion_yes.mean():.1%} ± {yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_REJECTED'].proportion_yes.std()/np.sqrt(len(yes_df[yes_df["Voter Type"]=="Regular wallet"][yes_df[yes_df["Voter Type"]=="Regular wallet"].status=='PROPOSAL_STATUS_REJECTED'])):.1%}

At most, regular wallets represented around 40% of the vote of 2 proposals, with most votes only having around 1% coming from regular users.
    """
)

chart_voting_power = (
    alt.Chart(yes_df)
    .mark_bar(binSpacing=0, opacity=0.65)
    .encode(
        alt.X("Voting Power", bin=alt.Bin(maxbins=25)),
        alt.Y(
            "count()",
            stack=None,
        ),
        alt.Order(
            "count(Voting Power)",
            sort="descending",
        ),
        alt.Color(
            "Voter Type",
        ),
        tooltip=[
            alt.Tooltip("Voter Type"),
            alt.Tooltip(
                "average(Voting Power)",
                title="Average Voting Power in bin, LUNA",
                format=",.0f",
            ),
            alt.Tooltip("count(Voting Power)", title="Proposals in bin", format=",.0f"),
        ],
    )
    .properties(width=800)
).interactive()

chart_proportion = (
    alt.Chart(yes_df)
    .mark_bar(binSpacing=0, opacity=0.65)
    .encode(
        alt.X(
            "proportion_yes",
            bin=alt.Bin(maxbins=25),
            title="Proportion voting Yes (binned)",
        ),
        alt.Y(
            "count()",
            stack=None,
        ),
        alt.Order(
            "count(proportion_yes)",
            sort="descending",
        ),
        alt.Color("Voter Type", legend=alt.Legend(orient="bottom")),
        tooltip=[
            alt.Tooltip("Voter Type"),
            alt.Tooltip(
                "average(proportion_yes)",
                title="Average Proportion voting Yes in bin",
                format=",.2%",
            ),
            alt.Tooltip(
                "count(proportion_yes)", title="Proposals in bin", format=",.0f"
            ),
        ],
    )
    .properties(width=800)
).interactive()
st.altair_chart(chart_voting_power & chart_proportion, use_container_width=True)

# compare the percentage of vals voting yes vs percentage of non-vals
sub_df = completed_df[
    [
        "proposal_id",
        "option",
        "voting_power",
        "non_val_voting_power",
        "val_voting_power",
        "title",
        "status",
        "voting_end_time",
    ]
]
sub_df["non_val_proportion"] = sub_df["non_val_voting_power"] / sub_df.groupby(
    ["proposal_id"]
)["non_val_voting_power"].transform("sum")
sub_df["val_proportion"] = sub_df["voting_power"] / sub_df.groupby(["proposal_id"])[
    "voting_power"
].transform("sum")
sub_df = (
    sub_df.fillna(0)
    .replace("PROPOSAL_STATUS_REJECTED", "Rejected")
    .replace("PROPOSAL_STATUS_PASSED", "Passed")
)
sub_df["Difference"] = sub_df["val_proportion"] - sub_df["non_val_proportion"]

yes_df2 = (
    sub_df[sub_df.option == "Yes"]
    .rename(
        columns={
            "val_proportion": "Validator",
            "non_val_proportion": "Regular wallet",
        }
    )
    .melt(
        id_vars=["proposal_id", "title", "status", "voting_end_time", "Difference"],
        value_vars=["Validator", "Regular wallet"],
        var_name="Voter Type",
        value_name="Voting Proportion",
    )
).sort_values(by=["Voter Type", "proposal_id"])

st.subheader("Validators vs. Non-Validators")


# TODO: work on this later?
st.write(
    """
Next we'll compare if validators and non-validators vote in similar ways.

For the most part, if there is a very low proportion of "Yes" votes, both groups vote similarly.
The same is true for when votes are overwhemingly Yes.
"""
)
chart_proportion = (
    alt.Chart(yes_df2)
    .mark_bar(binSpacing=0, opacity=0.65)
    .encode(
        alt.X(
            "Voting Proportion",
            bin=True,
            title="Proportion voting Yes (binned)",
        ),
        alt.Y(
            "count()",
            stack=None,
        ),
        alt.Order(
            "count(Voting Proportion)",
            sort="descending",
        ),
        alt.Color("Voter Type", legend=alt.Legend(orient="bottom")),
        tooltip=[
            alt.Tooltip("Voter Type"),
            alt.Tooltip(
                "average(Voting Proportion)",
                title="Average Proportion voting Yes in bin",
                format=",.2%",
            ),
            alt.Tooltip(
                "count(Voting Proportion)", title="Proposals in bin", format=",.0f"
            ),
        ],
    )
    .properties(width=800)
).interactive()
st.altair_chart(chart_proportion, use_container_width=True)

st.write(
    """
This is more clear in the two charts below.
The percentage voting Yes between validators and non-validators is shown, and generarally these two groups vote the same way (though some proposals had little or no particpation by non-validators)
"""
)
chart = (
    alt.Chart(yes_df2)
    .mark_bar()
    .transform_calculate(cat="datum['Voter Type'] + ': ' + datum.status")
    .encode(
        alt.X("proposal_id:N", axis=None),
        alt.Y(
            "Voting Proportion",
            axis=None,
            #  stack='center'
        ),
        alt.Color(
            "cat:N",
            title="Voter type and Proposal Status",
            scale=alt.Scale(range=["#172ad1", "#d17117", "#17d11d", "#d11755"]),
            legend=alt.Legend(orient="bottom"),
        ),
        tooltip=[
            alt.Tooltip("proposal_id", title="Proposal ID"),
            alt.Tooltip("title", title="Proposal Title"),
            alt.Tooltip("Voter Type"),
            alt.Tooltip(
                "Voting Proportion", title="Proportion voting Yes", format=".1%"
            ),
            alt.Tooltip("status", title="Status"),
            alt.Tooltip("voting_end_time", title="Vote end date"),
        ],
    )
    .properties(width=800)
)


st.altair_chart(chart, use_container_width=True)


st.write(
    f"""
The difference in proportion voting Yes between validators and non-validators is shown below for Passed and Rejected votes.

The mean difference is **{sub_df[sub_df.option == "Yes"].Difference.mean():.1%}** for all proposals, **{sub_df[sub_df.option == "Yes"][sub_df["status"] == "Passed"].Difference.mean():.1%}** for Passed proposals and **{sub_df[sub_df.option == "Yes"][sub_df["status"] ==  "Rejected"].Difference.mean():.1%}** for Rejected proposals.

While the two groups generally vote in similar ways, it seems there is more divergence when the vote is rejected.
"""
)
chart2 = (
    alt.Chart(sub_df[sub_df.option == "Yes"])
    .mark_bar()
    .encode(
        alt.X("proposal_id:N", axis=None),
        alt.Y(
            "Difference",
            axis=None,
            #  stack='center'
        ),
        alt.Color("status", title="Vote Status", legend=alt.Legend(orient="bottom")),
        tooltip=[
            alt.Tooltip("proposal_id", title="Proposal ID"),
            alt.Tooltip("title", title="Proposal Title"),
            alt.Tooltip(
                "Difference",
                title="Difference: Validator and Non-Validator Voting Yes",
                format=".1%",
            ),
            alt.Tooltip("status", title="Status"),
            alt.Tooltip("voting_end_time", title="Vote end date"),
        ],
    )
).interactive()
overlay = pd.DataFrame({"y": [0.1, -0.1]})
hline = alt.Chart(overlay).mark_rule(color="red").encode(y="y:Q")
mean = (
    alt.Chart(sub_df[sub_df.option == "Yes"])
    .mark_rule(color="green")
    .encode(y="mean(Difference):Q")
)
st.altair_chart(chart2 + hline + mean, use_container_width=True)

st.header("Proposal Details")
status_dict = {
    "Voting (Active)": "PROPOSAL_STATUS_VOTING_PERIOD",
    "Deposit (Active)": "PROPOSAL_STATUS_DEPOSIT_PERIOD",
    "Rejected": "PROPOSAL_STATUS_REJECTED",
    "Passed": "PROPOSAL_STATUS_PASSED",
    "Completed (Passed or Rejected)": "Completed (Passed or Rejected)",
    "All": "All",
}
col1, col2 = st.columns([1, 3])
proposal_status = col1.radio("Proposal status", status_dict.keys(), 0)


proposal_titles, sub_df = get_proposal_info(proposal_df, status_dict[proposal_status])
proposals = col2.selectbox("Proposals", proposal_titles, 0)

cols = st.columns(2)
if proposals != "All":
    sub_df = sub_df[sub_df.proposal_id == int(proposals.split(":")[0])].reset_index(
        drop=True
    )
    cols = st.columns(1)

for i, x in sub_df.iterrows():

    with cols[i % 2].expander(label=f"{x.proposal_id}: {x.title}"):
        st.subheader(f"Proposal {x.proposal_id}: {x.title}")
        st.write(
            f"[Terra Station Link](https://station.terra.money/proposal/{x.proposal_id})"
        )
        st.write(f"**Description**:\n\n{x.description}")
        "---"
        st.write(
            f"**Status**: {list(status_dict.keys())[list(status_dict.values()).index(x.status)]}"
        )

        if x.status in ["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"]:
            st.write(f"**Vote Start Date**: {x['voting_start_time']:%Y-%m-%d}")
            st.write(f"**Vote End Date**: {x['voting_end_time']:%Y-%m-%d}")
        if x.status == "PROPOSAL_STATUS_VOTING_PERIOD":
            st.write(f"**Vote Start Date**: {x['voting_start_time']:%Y-%m-%d}")
        if x.status == "PROPOSAL_STATUS_DEPOSIT_PERIOD":
            st.write(f"**Submit Time*: {x['submit_time']:%Y-%m-%d}")

st.header("Methods")
st.write(
    """
The non-validator voting power was derived from [this query](https://app.flipsidecrypto.com/velocity/queries/20f89eaa-e7f5-42b9-834f-45027923775a).
Any gov_vote where there is no label was treaded as a non-validator.
The voting power was derived from the daily balance of staked LUNA from that day.
This is due to an issue where the `Voting_Power` column of the `terra.gov_vote` table had a lot of null values.

For validator voting, the [Terra LCD](https://lcd.terra.dev/swagger/) was used to capture information on the governance proposals.
Validator vote counts were derived by subtracting the non-validator votes from the total votes per each proposal.

In the `terra.gov_vote` table, the voting power is not accurate for the validator address-- when it is not null, the value is the amount in the terra address owned by the validator, and not the total amount delegated to that validator.

Thanks to user hfuhruhurr#8781 (on Flipside Crypto Discord) for discussions on this topic!
"""
)
