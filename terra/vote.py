# # Votes, Votes, Votes
# > On average, how much voting power (in Luna) was used to vote 'YES' for governance proposals? Out of this, how much Luna comes from validators vs regular wallets?

from ctypes import alignment
from heapq import merge
from re import sub
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
open_proposals = proposal_df[proposal_df.status=="PROPOSAL_STATUS_VOTING_PERIOD"]


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

st.subheader("Past votes")
st.write(
"""
Results of past governance votes are shown below, with both thevote perentages and the amount of LUNA used for each voting option.
"""
)
completed_df = merged_df[merged_df["status"].isin(["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"])]

chart_percentage = alt.Chart(completed_df).mark_bar().encode(
    alt.X("proposal_id:N",axis=None, title="Proposals"),
    alt.Y("voting_power", stack='normalize', title="Vote Percentage"),
    alt.Color('option', sort=['Yes', 'No', 'NoWithVeto', 'Abstain'], legend=alt.Legend(orient='bottom'), title='Voting Option'),
    tooltip= [
        alt.Tooltip('proposal_id', title="Proposal ID"),
        alt.Tooltip('title', title='Proposal Title'),
        alt.Tooltip('option', title='Option'),
        alt.Tooltip('voting_power', title='Voting Power, LUNA', format=',.0f'),
        alt.Tooltip('status', title='Status'),
        alt.Tooltip('voting_end_time', title='Vote end date'),
    ]
).properties(width=800)
chart_values = alt.Chart(completed_df).mark_bar().encode(
    alt.X("proposal_id:N",axis=None, title="Proposals"),
    alt.Y("voting_power", title="Voting Power (LUNA)"),
    alt.Color('option', sort=['Yes', 'No', 'NoWithVeto', 'Abstain']),
    tooltip= [
        alt.Tooltip('proposal_id', title="Proposal ID"),
        alt.Tooltip('title', title='Proposal Title'),
        alt.Tooltip('option', title='Option'),
        alt.Tooltip('voting_power', title='Voting Power, LUNA', format=',.0f'),
        alt.Tooltip('status', title='Status'),
        alt.Tooltip('voting_end_time', title='Vote end date'),
    ]
).properties(width=800)
st.altair_chart(chart_percentage & chart_values, use_container_width=True)


total_proposals = len(proposal_df.proposal_id.unique())
completed_votes = len(proposal_df[
    proposal_df.status.isin(["PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_PASSED"])])
no_vote = len(proposal_df[proposal_df.status=="PROPOSAL_STATUS_DEPOSIT_PERIOD"])
open_proposals = len(proposal_df[proposal_df.status=="PROPOSAL_STATUS_VOTING_PERIOD"])
rejected_proposals = len(proposal_df[proposal_df.status=="PROPOSAL_STATUS_REJECTED"])
passed_proposals = len(proposal_df[proposal_df.status=="PROPOSAL_STATUS_PASSED"])


st.write("To make a governance proposal, a minimum deposit threshold of 50 LUNA needs to be met. Without this, the proposal will not be voted upon")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Proposals", total_proposals)
col2.metric("Completed Votes", completed_votes)
col3.metric("Proposals without votes", no_vote)
col4.metric("Open Proposals", open_proposals)

col1.metric("Passed Proposals", passed_proposals)
col2.metric("Passed Percentage", f"{passed_proposals/completed_votes:.1%}")
col3.metric("Rejected Proposals", rejected_proposals)
col4.metric("Rejected Percentage", f"{rejected_proposals/completed_votes:.1%}")


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
if proposals != 'All':
    sub_df = sub_df[sub_df.proposal_id == int(proposals.split(':')[0])].reset_index(drop=True)
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

        if x.status in ["PROPOSAL_STATUS_REJECTED","PROPOSAL_STATUS_PASSED"]:
            st.write(f"**Vote Start Date**: {x['voting_start_time']:%Y-%m-%d}")
            st.write(f"**Vote End Date**: {x['voting_end_time']:%Y-%m-%d}")
        if x.status == "PROPOSAL_STATUS_VOTING_PERIOD":
            st.write(f"**Vote Start Date**: {x['voting_start_time']:%Y-%m-%d}")
        if x.status == "PROPOSAL_STATUS_DEPOSIT_PERIOD":
            st.write(f"**Submit Time*: {x['submit_time']:%Y-%m-%d}")

