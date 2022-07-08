import datetime
import altair as alt
import pandas as pd
import streamlit as st

import near_info

st.set_page_config(page_title="Citizens of NEAR: Active USers", page_icon="🌆")
st.title("Citizens of NEAR: Active Users")
st.caption(
    """
If NEAR were a city, who would the citizens be?

Let's look at the active users of NEAR, and examine any trends or outliers in the last 90 days
"""
)

st.header("Definitions and Introduction")
f"""
We want examine how users interact with the [**NEAR** blockchain](https://near.org/) and compare it to usage of several other popular blockchains:
- Ethereum
- Solana
- Algorand
- Polygon

This analysis will focus on data from the past **90 days**, acquired from Flipside Crypto (see [Methods](#methods) below for more info).
The 90 day time period covers a period when NEAR was at a high, through the crash of LUNA and widespread insolvency issues occurring in early July 2022.

We'll look at 3 types of users:
- **All Users**: Addresses which have made at any time during our analysis period (90 days)
- **Active Users**: Addresses which have made a transaction in the past **30 days**
- **Inactive Users**: Addresses which have made a transaction in the past 90 days, but have **not** made a transaction in the past 30 days

"Users" in all cases are addresses which sign a transaction, with no attempt to separate smart contracts or other non-human address type from actual human users.


Active users are still interacting on their respective blockchains regardless of the market conditions.
Inactive users, on the other hand, have stopped their activity over the last month as sentiments are more bearish.

**NOTE:** Analysis is written on 7 July 2022, though data will be updated daily.
Some text components of this analysis may become out of date, but numerical information and figures will use the latest data.
"""


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


st.header("A look at NEAR")
st.subheader("User data")
f"""
Let's look at the Daily User Counts of NEAR compared to other blockchains.
The left chart shows **All Users**, and the right shows **Active Users only**-- note the log scale!

Trends are similar between both charts, with Solana having by far the most Users, Polygon and Ethererum with the next most at comparable levels, followed by Algorand.
NEAR has the least Users, around half of Algorand.
"""
all_user_chart = near_info.alt_line_chart(user_data, "all_users").properties(width=200)
active_user_chart = near_info.alt_line_chart(user_data, "active_users").properties(
    width=200
)
combined = alt.hconcat(all_user_chart, active_user_chart)
st.altair_chart(combined, use_container_width=True)

f"""
Over the 90 day time period NEAR has:
- an average daily user count of **{int(mean_90d.all_users['NEAR']):,}**
- **{int(mean_90d.active_users['NEAR']):,}** of which are Active users.

In the past 30 days, the average number of daily users for NEAR is **{int(mean_30d.active_users['NEAR']):,}**.
"""

col1, col2 = st.columns([1, 1])
with col1:
    st.write("**Last 90 days (mean)**")
    st.dataframe(mean_90d)
with col2:
    st.write("**Last 30 days (mean)**")
    st.dataframe(mean_30d)
    "(All users interacting in this time period are active users)"

f"""
If we look back at the first 60 days of our time period, we can get an idea of whether users have been interacting on chain for a longer period of time, or are newer to the ecosystem.

NEAR has among the highest percentage of Active Users to Total Users (**{mean_first_60d.active_users_proportion["NEAR"]:.2%}**).
This means that a large proportion of users currently active have been using the blockchain throughout the entire period.

In comparison, Solana has a low percentage of Active Users to Total Users (**{mean_first_60d.active_users_proportion["Solana"]:.2%}**).
Only a small proportion of users currently active were using Solana 2-3 months ago.
"""
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
f"""
We'll now look at Daily Transaction data, with the left chart showing **All Users**, and the right showing **Active Users only** (again in log scale)

Solana, again, has by far the highest number of transactions (> 20 million per day on average!).
This is followed by Polygon with around 2.5 million per day, and Ethereum, Near, and Algorand in the 0.5 million-1 million transaction per day range.
"""
all_user_tx_chart = near_info.alt_line_chart(
    user_data,
    "all_users_tx",
).properties(width=200)
active_user_tx_chart = near_info.alt_line_chart(
    user_data,
    "active_users_tx",
).properties(width=200)
combined_tx = alt.hconcat(all_user_tx_chart, active_user_tx_chart)
st.altair_chart(combined_tx, use_container_width=True)

f"""
Over the 90 day time period NEAR has:
- an average daily transaction count **{int(mean_90d_tx.all_users_tx['NEAR']):,}**
- **{int(mean_90d_tx.active_users_tx['NEAR']):,}** of which are from Active users.

In the past 30 days, the average number of daily transactions for NEAR is **{int(mean_30d_tx.active_users_tx['NEAR']):,}**.
"""

col1, col2 = st.columns([1, 1])
with col1:
    st.write("**Last 90 days (mean)**")
    st.dataframe(mean_90d_tx)
with col2:
    st.write("**Last 30 days (mean)**")
    st.dataframe(mean_30d_tx)
    "(All users interacting in this time period are active users)"

f"""
A much higher overall proportion of daily transactions come from users still currently active.
In general around 80-90% of transactions from 2-3 months ago come from users still currently active.
The exception to this is Ethereum, with only **{mean_first_60d_tx.active_users_tx_proportion["Ethereum"]:.2%}.
Since it is the largest chain by total value locked (TVL), market sentiments could have a larger effect on its users.
Addresses accounting for large numbers of Ethereum transactions in the past may have cut back on usage in this recent downturn
**
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


f"""
Last, we'll look at Daily Transactions per User, comparing All Users and active Users.

Algorand has the highest number of Daily Transactions per User, followed by NEAR and Solana.
Polygon has fewer Transactiosn per User, while Ethereum has by far the least.
"""

all_user_tx_per_user_chart = near_info.alt_line_chart(
    user_data, "tx_per_all_users", log_scale=False
).properties(width=200)
active_user_tx_per_user_chart = near_info.alt_line_chart(
    user_data, "tx_per_active_users", log_scale=False
).properties(width=200)
combined_tx = alt.hconcat(all_user_tx_per_user_chart, active_user_tx_per_user_chart)
st.altair_chart(combined_tx, use_container_width=True)

f"""
Over the 90 day time period NEAR has:
- an average daily transaction count per user is **{mean_90d_tx_per_user.tx_per_all_users['NEAR']:.2f}** for All Users, and
- **{mean_90d_tx_per_user.tx_per_active_users['NEAR']:.2f}** for Active Users only.

In the past 30 days, the average number of daily transactions for NEAR is **{mean_30d_tx_per_user.tx_per_active_users['NEAR']:.2f}**.
"""

col1, col2 = st.columns([1, 1])
with col1:
    st.write("**Last 90 days (mean)**")
    st.dataframe(mean_90d_tx_per_user)
with col2:
    st.write("**Last 30 days (mean)**")
    st.dataframe(mean_30d_tx_per_user)
    "(All users interacting in this time period are active users)"

"""
For all chains, Active Users have a higher transaction count per user than All Users in this time period.
"""

st.header("So... what city is NEAR?")
"""
NEAR has the following characteristics:
- Low population (small number of Active Users)
- Old population (higher porportion of users over the last 90 days are Active Users)
- Dense population (low average transactions per day, but high numbers of transactions per users)

With this in mind, NEAR would be a small city in Europe, with a high density in a country with a aging population.

Based on extensive research (using sources [here](https://en.wikipedia.org/wiki/List_of_cities_proper_by_population_density) and [here](https://www.worlddata.info/average-age.php)), an example city would be **[Neapoli, Thessaloniki, Greece
](https://en.wikipedia.org/wiki/Neapoli,_Thessaloniki)**!
"""

st.header("Methods")
with st.expander("Queries and Methods"):

    "Data is from Flipside Crytpo, using the following queries:"
    for k, v in near_info.query_information.items():
        x = f"- [{k}]({v['query']})"
        x
    """
    The `transaction` table from each of the chains was used, counting the equivalent of a `tx_id` as a unique transaction, and `from_address` or `signer` as a user.

    Future work on this analysis can improve this process, by filtering out addresses which are known to be associated with smart contracts or other non-human addresses.

    Additionally, more quantitative metrics can be used for determining the city of different blockchains.
    """

# Q1. If NEAR were a city, who would the citizens be?
# Provide a clear definition for “active users” (for example: users who have transacted at least once in the past 30 days).
# Then, visualize NEAR’s active users over the past 90 days.
# Concisely document any trends or outliers that you observe and provide a 1-2 paragraph summary of active users on NEAR.
