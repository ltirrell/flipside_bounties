import datetime

import altair as alt
import pandas as pd
import streamlit as st

import near_info
from journey_utils import *

alt.data_transformers.disable_max_rows()

st.set_page_config(
    page_title="Citizens of NEAR: The Journeymen", page_icon="🌆", layout="wide"
)

st.title("Citizens of NEAR: The Journeymen")
st.caption(
    """
It's all about the journey, not the destination. Investigating the NEAR User jouney
"""
)
st.write(
    """Our NEAR user journey will focus on 3 aspects:
- the first transactions of NEAR users,
- what NEAR users do after bridging assets from Ethereum,
- and a comparison of some User and Transaction metrics with other blockchains.
"""
)

with st.expander("Data Sources and Methods"):
    st.header("Methods")
    f"""
    Data was acquired from Flipside Crypto's NEAR tables.
    Crosschain data is based off of previous analysis (see [here](https://ltirrell-flipside-bounties-nearcitizens-of-near-users-xtxglz.streamlitapp.com/)), using the following queries:
    """
    for k, v in near_info.query_information.items():
        x = f"- [{k}]({v['query']})"
        x
    """
    The `transaction` table from each of the chains was used, counting the equivalent of a `tx_id` as a unique transaction, and `from_address` or `signer` as a user.

    The query used for the Rainbow bridge section was heavily influenced by [excellent work](https://app.flipsidecrypto.com/dashboard/the-rainbow-bridge-Ai9j6g) from Discord user `mhm#1465`, as well as discussions with [@pinehearst_](https://twitter.com/pinehearst_)🌲.

    This, and other query information can be found here:
    """
    for k, v in query_information.items():
        x = f"- [{k}]({v['query']})"
        x

fs_data = load_data()

st.header("First Transactions")
st.caption('"A journey of a thousand miles begins with a single step" -Laozi')
st.write(
    """
What do NEAR users do first when they interact with the blockchain?
Our analysis will focus on **currently active users** (making a transction in the past 30 days), whose account was **created after 1-Sep-2021** (Flipside Crypto data is limited to this point).
    """
)
st.subheader("New User information")
near_user = fs_data["near_user"].copy()
most_recent_full_day = near_user.sort_values(by="CREATION_DATE").iloc[-2]
c1, c2 = st.columns([1, 3])
c1.write(
    f"**Metrics for the most recent full day ({most_recent_full_day.CREATION_DATE})**"
)
c1.metric(f"New Users", f"{int(most_recent_full_day.NEW_USERS):,}")
c1.metric(f"Cumulative New Users", f"{int(most_recent_full_day.CUMULATIVE_USERS):,}")
c1.metric(
    f"Cumulative Average Daily New Users",
    f"{float(most_recent_full_day.CUMULATIVE_AVERAGE_DAILY_NEW_USERS):,.1f}",
)
c2.altair_chart(alt_user_chart(near_user), use_container_width=True)

st.subheader("First Transaction: Method Name")
"""
We can see which type of transaction is done first by a user. We can choose between two transaction:
- `Received`: the first transaction where the user's address is the *transaction receiver*. This means a user received something, or another address acted upon their address.
- `Sent`: the first transaction where the user's address is the *transaction sender*. This means a user initiated or sent out a transaction.
"""
first_method = fs_data["first_method"].copy()
first_method["USER_COUNT"] = pd.to_numeric(first_method["USER_COUNT"])
c1, c2 = st.columns([3, 1])
tx_type = c2.selectbox(
    "Choose transaction type:",
    first_method.TX_TYPE.unique(),
    format_func=lambda x: x.title(),
    key="first_method",
)
c1.altair_chart(alt_ordered_bar(first_method, tx_type), use_container_width=True)


st.header("Crossing the Rainbow Bridge")
st.write(
    "NEAR users often begin their journey by crossing the [Rainbow Bridge](https://rainbowbridge.app/transfer), moving assets from Ethereum onto the NEAR blockchain. We'll investigate what these users did once their assets are in NEAR, and analyze the source of these transactions from Ethereum."
)
rainbow = fs_data["rainbow"].copy()
rainbow = rainbow.replace("nan", pd.NA)
rainbow["NUMBER_OF_BRIDGE_TX"] = pd.to_numeric(rainbow["NUMBER_OF_BRIDGE_TX"])
rainbow["TOTAL_AMOUNT_BRIDGED"] = pd.to_numeric(rainbow["TOTAL_AMOUNT_BRIDGED"])
rainbow["AVERAGE_AMOUNT_BRIDGED"] = pd.to_numeric(rainbow["AVERAGE_AMOUNT_BRIDGED"])
rainbow["NUMBER_OF_TOKENS_BRIDGED"] = pd.to_numeric(rainbow["NUMBER_OF_TOKENS_BRIDGED"])
rainbow["TOTAL_SENDERS"] = pd.to_numeric(rainbow["TOTAL_SENDERS"])
rainbow["TOTAL_RECEIVERS"] = pd.to_numeric(rainbow["TOTAL_RECEIVERS"])
rainbow["LATEST_BALANCE_ETHEREUM"] = pd.to_numeric(rainbow["LATEST_BALANCE_ETHEREUM"])

rainbow_totals = rainbow[rainbow.VARIABLE == "total"].reset_index(drop=True).iloc[0]

rainbow_by_date = rainbow[rainbow.VARIABLE == "date"].reset_index(drop=True)
rainbow_by_date["Date"] = pd.to_datetime(rainbow_by_date.GROUPER)
rainbow_by_date = rainbow_by_date.sort_values(by="Date")

rainbow_by_address = rainbow[
    (rainbow.VARIABLE == "sender") | (rainbow.VARIABLE == "receiver")
].reset_index(drop=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Total Ethereum -> NEAR bridge transactions",
    f"{rainbow_totals.NUMBER_OF_BRIDGE_TX:,}",
)
c2.metric("Total Senders (Ethereum addresses)", f"{rainbow_totals.TOTAL_SENDERS:,}")
c3.metric("Total Senders (NEAR addresses)", f"{rainbow_totals.TOTAL_RECEIVERS:,}")
c4.metric(
    "Unique Tokens Bridged (Ethereum -> NEAR)",
    f"{rainbow_totals.NUMBER_OF_TOKENS_BRIDGED:,}",
)
c1.metric(
    "Total Value Bridged, Ethereum -> NEAR",
    f"${rainbow_totals.TOTAL_AMOUNT_BRIDGED:,.2f}",
)
c2.metric(
    "Average Value Bridged per Transactuin, Ethereum -> NEAR bridge",
    f"${rainbow_totals.AVERAGE_AMOUNT_BRIDGED:,.2f}",
)
c3.metric(
    "Average Current Account Balance of Ethereum Addresses",
    f"${rainbow_totals.LATEST_BALANCE_ETHEREUM:,.2f}",
)

st.write(
    "We can explore the above metrics on a daily basis. Any Amount is in USD, and `Latest Balance Ethereum` is the average most recent account balance of Ethereum accounts that used the Rainbow bridge that day."
)
c1, c2 = st.columns([1, 3])
metric = c1.selectbox(
    "Choose a metric",
    rainbow_by_date.columns.drop(["GROUPER", "VARIABLE", "Date"]).values,
    format_func=lambda x: x.replace("_", " ").title(),
    key="date_metric",
)
c2.altair_chart(alt_date_area(rainbow_by_date, metric), use_container_width=True)


st.write(
    "The top Rainbow Bridge receivers are shown below, for each of the selected metrics."
)
c1, c2 = st.columns([3, 1])
metric = c2.selectbox(
    "Choose a metric",
    rainbow_by_address.columns.drop(["GROUPER", "VARIABLE", "TOTAL_RECEIVERS"]).values,
    format_func=lambda x: x.replace("_", " ").title(),
    key="address_metric",
)
ordering = c2.radio(
    "Choose sort order",
    [True, False],
    format_func=lambda x: "Ascending" if x else "Descending",
    index=1,
)
c1.altair_chart(
    alt_ordered_bar_receiver(
        rainbow_by_address[rainbow_by_address.VARIABLE == "receiver"], metric, ordering
    ),
    use_container_width=True,
)


st.write(
    "We can look at the same metriics for Rainbow Bridge senders. Because we have the latest account balance of the senders, the [Gini coeffecient](https://github.com/oliviaguest/gini) can be calculated. This shows the income inequality between a set of address (where 1 is high inequality and 0 is high equality)"
)
g = gini(
    rainbow_by_address[rainbow_by_address.VARIABLE == "sender"]
    .LATEST_BALANCE_ETHEREUM.dropna()
    .values
)
c1, c2 = st.columns([1, 3])
metric = c1.selectbox(
    "Choose a metric",
    rainbow_by_address.columns.drop(["GROUPER", "VARIABLE", "TOTAL_SENDERS"]).values,
    format_func=lambda x: x.replace("_", " ").title(),
    key="address_metric_sender",
)
ordering = c1.radio(
    "Choose sort order",
    [True, False],
    format_func=lambda x: "Ascending" if x else "Descending",
    index=1,
    key="address_metric_sender",
)
c1.metric("Gini Coeffecient", f"{g:.3f}")
c2.altair_chart(
    alt_ordered_bar_sender(
        rainbow_by_address[rainbow_by_address.VARIABLE == "sender"], metric, ordering
    ),
    use_container_width=True,
)

st.subheader("NEAR Bridger: user interactions")
near_interactions = fs_data["near_interactions"].copy()
near_interactions["VALUE"] = pd.to_numeric(near_interactions["VALUE"])
num_recievers = (
    near_interactions[near_interactions.VARIABLE == "num_receivers"]
    .rename(
        columns={"GROUPER": "Near User", "VALUE": "Number of Addresses Interacted With"}
    )
    .sort_values(by="Number of Addresses Interacted With", ascending=False)
    .reset_index(drop=True)
)
num_methods = (
    near_interactions[near_interactions.VARIABLE == "num_methods"]
    .rename(columns={"GROUPER": "Near User", "VALUE": "Number of Methods Used"})
    .sort_values(by="Number of Methods Used", ascending=False)
    .reset_index(drop=True)
)
num_users = (
    near_interactions[near_interactions.VARIABLE == "num_users"]
    .rename(
        columns={"GROUPER": "Near Transaction Receiver", "VALUE": "Number of Users"}
    )
    .sort_values(by="Number of Users", ascending=False)
    .reset_index(drop=True)
)


tx_receivers = len(num_users["Near Transaction Receiver"].unique())
near_users = len(num_methods["Near User"].unique())

c1, c2, c3 = st.columns(3)
c1.write(
    "Let's examine what addresses the NEAR bridgers interact with after moving assets from Ethereum."
)
c2.metric("Number of Near Bridgers", near_users)
c3.metric("Number of Addresses Interacted with", tx_receivers)

st.write(
    """We'll look at:
- the number of addresses a bridger interacted with,
- the number of methods used by a bridger,
- and the number of users interacting with specific NEAR addresses
"""
)

c1, c2 = st.columns([3, 1])
c1.altair_chart(
    alt_bar_interactions(
        num_recievers,
        "Near User",
        "Number of Addresses Interacted With",
        "User metrics: Number of Addresses Interacted With",
    )
)
c2.metric(
    "Average number of addresses interacted with",
    f"{num_recievers['Number of Addresses Interacted With'].mean():.2f}",
)
c1, c2 = st.columns([1, 3])
c1.metric(
    "Average number of Methods used",
    f"{num_methods['Number of Methods Used'].mean():.2f}",
)
c2.altair_chart(
    alt_bar_interactions(
        num_methods,
        "Near User",
        "Number of Methods Used",
        title="User metrics: Number of Methods Used",
    )
)
c1, c2 = st.columns([3, 1])
c1.altair_chart(
    alt_bar_interactions(
        num_users,
        "Near Transaction Receiver",
        "Number of Users",
        title="Protocol Metrics: Number of Users Interacting with each protocol",
    )
)
c2.metric(
    "Average Number of Users, per Protocol",
    f"{num_users['Number of Users'].mean():.2f}",
)


st.header("Crosschain comparison")
st.write(
    f"""
We want examine how users interact with the [**NEAR** blockchain](https://near.org/) and compare it to usage of several other popular blockchains:
- Ethereum
- Solana (only looking at the past 30 days)
- Algorand
- Polygon

This analysis will focus on data from the past **90 days**.

We'll look at 3 types of users:
- **All Users**: Addresses which have made at any time during our analysis period (90 days)
- **Active Users**: Addresses which have made a transaction in the past **30 days**
- **Inactive Users**: Addresses which have made a transaction in the past 90 days, but have **not** made a transaction in the past 30 days

"Users" in all cases are addresses which sign a transaction, with no attempt to separate smart contracts or other non-human address type from actual human users.


Active users are still interacting on their respective blockchains regardless of the market conditions.
Inactive users, on the other hand, have stopped their activity over the last month as sentiments are more bearish or unpredictable.
"""
)
user_data = near_info.load_data()

user_data_last_30 = user_data[
    user_data.datetime
    >= (pd.to_datetime(datetime.date.today()) - pd.Timedelta(days=30))
].copy()
user_data_first_60 = user_data[
    user_data.datetime < (pd.to_datetime(datetime.date.today()) - pd.Timedelta(days=30))
].copy()

mean_90d = user_data.groupby(["blockchain"])[["all_users", "active_users"]].mean()
mean_30d = user_data_last_30.groupby(["blockchain"])[["active_users"]].mean()
mean_first_60d = user_data_first_60.groupby(["blockchain"])[
    ["active_users_proportion"]
].mean()

mean_90d_tx = user_data.groupby(["blockchain"])[
    ["all_users_tx", "active_users_tx"]
].mean()
mean_30d_tx = user_data_last_30.groupby(["blockchain"])[["active_users_tx"]].mean()
mean_first_60d_tx = user_data_first_60.groupby(["blockchain"])[
    ["active_users_tx_proportion"]
].mean()

mean_90d_tx_per_user = user_data.groupby(["blockchain"])[
    ["tx_per_all_users", "tx_per_active_users"]
].mean()
mean_30d_tx_per_user = user_data_last_30.groupby(["blockchain"])[
    ["tx_per_active_users"]
].mean()

st.subheader("User Data")
st.write(
    "We can see the Average Daily Users across various blockchains below, divided between all users (from the past 90d) and focusing on users who are currently active (within the last 30d)"
)


c1, c2, c3 = st.columns([2, 1, 1])
all_user_chart = near_info.alt_line_chart(user_data, "all_users").properties(
    width=200, height=420
)
active_user_chart = near_info.alt_line_chart(user_data, "active_users").properties(
    width=200, height=420
)
combined = alt.hconcat(all_user_chart, active_user_chart)
c1.altair_chart(combined, use_container_width=True)
c2.metric("NEAR average daily users (past 90d)", f"{int(mean_90d.all_users['NEAR']):,}")
c2.metric(
    "NEAR average daily users who are still active",
    f"{int(mean_90d.active_users['NEAR']):,}",
)
c2.metric(
    "NEAR average daily users (past 30d)", f"{int(mean_30d.active_users['NEAR']):,}"
)
c3.write("**Last 90 days (mean)**")
c3.dataframe(mean_90d)
c3.write("**Last 30 days (mean)**")
c3.dataframe(mean_30d)


"""We can see the proporption of currently active users who were active 60-90 days ago on various blockchains, to get an idea of whether users have been interacting on chain for a longer period of time, or are newer to the ecosystem."""
proportion_chart = near_info.alt_line_chart(
    user_data_first_60, "active_users_proportion", log_scale=False
)
col1, col2 = st.columns([3, 1])
with col1:
    st.altair_chart(proportion_chart, use_container_width=True)
with col2:
    st.write("**Proportion of active users (mean)**")
    st.dataframe(mean_first_60d)

st.subheader("Transaction data")
st.write(
    "Additionally, we can do the same comparison with daily transaction counts across various blockchains, again divided between all users (from the past 90d) and focusing on users who are currently active (within the last 30d)"
)
c1, c2, c3 = st.columns([2, 1, 1])
all_user_tx_chart = near_info.alt_line_chart(
    user_data,
    "all_users_tx",
).properties(width=200, height=420)
active_user_tx_chart = near_info.alt_line_chart(
    user_data,
    "active_users_tx",
).properties(width=200, height=420)
combined_tx = alt.hconcat(all_user_tx_chart, active_user_tx_chart)
c1.altair_chart(combined_tx, use_container_width=True)

c2.metric(
    "NEAR average daily transaction count (past 90d)",
    f"{int(mean_90d_tx.all_users_tx['NEAR']):,}",
)
c2.metric(
    "NEAR average daily transaction count, from active users",
    f"{int(mean_90d_tx.active_users_tx['NEAR']):,}",
)
c2.metric(
    "NEAR average daily transaction count (past 30d)",
    f"{int(mean_30d_tx.active_users_tx['NEAR']):,}",
)
c3.write("**Last 90 days (mean)**")
c3.dataframe(mean_90d_tx)
c3.write("**Last 30 days (mean)**")
c3.dataframe(mean_30d_tx)

f"""
The proportion of transactions from currently active users who were active 60-90 days ago on various blockchains is shown here:
"""
proportion_chart = near_info.alt_line_chart(
    user_data_first_60, "active_users_tx_proportion", log_scale=False
)
col1, col2 = st.columns([3, 1])
with col1:
    st.altair_chart(proportion_chart, use_container_width=True)
with col2:
    st.write("**Proportion of active users (mean)**")
    st.dataframe(mean_first_60d_tx)


st.subheader("Daily transactions per User")
st.write(
    "Finally, let's compare the number of daily transactions per user, divided between all users (from the past 90d) and focusing on users who are currently active (within the last 30d)"
)
c1, c2, c3 = st.columns([2, 1, 1])

all_user_tx_per_user_chart = near_info.alt_line_chart(
    user_data, "tx_per_all_users", log_scale=False
).properties(width=200, height=420)
active_user_tx_per_user_chart = near_info.alt_line_chart(
    user_data, "tx_per_active_users", log_scale=False
).properties(width=200, height=420)
combined_tx = alt.hconcat(all_user_tx_per_user_chart, active_user_tx_per_user_chart)

c1.altair_chart(combined_tx, use_container_width=True)
c2.metric(
    "NEAR average daily transaction count per user (past 90d)",
    f"{mean_90d_tx_per_user.tx_per_all_users['NEAR']:.2f}",
)
c2.metric(
    "NEAR average daily transaction count per user, from active users",
    f"{int(mean_90d_tx.active_users_tx['NEAR']):,}",
)
c2.metric(
    "NEAR average daily transaction count (past 30d)",
    f"{mean_30d_tx_per_user.tx_per_active_users['NEAR']:.2f}",
)
c3.write("**Last 90 days (mean)**")
c3.dataframe(mean_90d_tx_per_user)
c3.write("**Last 30 days (mean)**")
c3.dataframe(mean_30d_tx_per_user)


with st.expander("Data tables"):
    st.subheader("Crosschain data")
    user_data
    for k, v in fs_data.items():
        st.subheader(k)
        v
