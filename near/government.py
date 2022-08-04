import pandas as pd
import streamlit as st
from dateutil import parser
from shroomdk import errors

from gov_utils import *

st.set_page_config(
    page_title="Citizens of NEAR: Local Government", page_icon="🌆", layout="wide"
)

st.title("Citizens of NEAR: Local Government")
st.caption(
    """
Every city has its governors, and NEAR as ran by its validators.

Exploring NEAR governance, with a focus on the current validator set.
"""
)


st.header("State of the Unions")
# drop_inactive = st.checkbox("Remove inactive validators from analysis. NOTE: this is causing issues with data analysis and is being actively debugged, so it may not work...")

blocktimes = get_blocktimes()
status = get_status()
validators = get_validators()
# not using for now
# blocks = get_blocks()
# epochs = get_epochs()
# block_height = status["last_block_height"] # don't care about this right now
last_update = parser.parse(status["last_block_time"]).strftime("%Y-%m-%d %H:%M:%S %Z")
avg_blocktime = blocktimes["avg"]
validator_names = validators.account_id
total_staked = validators["Stake (NEAR)"].sum()

vals_sorted_stake = validators.sort_values(
    by="Stake (NEAR)", ascending=False
).reset_index(drop=True)
vals_sorted_stake["Cumulative Stake (NEAR)"] = vals_sorted_stake[
    "Stake (NEAR)"
].cumsum()
vals_sorted_stake["Proportion of Stake"] = (
    vals_sorted_stake["Stake (NEAR)"] / total_staked
)
nakamoto_line = 0.33 * total_staked

nakamoto_coeffecient = (
    vals_sorted_stake[
        vals_sorted_stake["Cumulative Stake (NEAR)"] > nakamoto_line
    ].index[0]
    + 1
)
gini_coeffecient = gini(vals_sorted_stake["Stake (NEAR)"].to_numpy())


st.subheader("Overall blockchain statistics")
c1, c2, c3 = st.columns(3)
c1.metric("Number of Validators", len(validator_names))
c2.metric("Average block time (s)", f"{avg_blocktime:.2f}")
c3.metric("Last updated", last_update)
c1.metric("Total Staked NEAR", f"{total_staked:,.2f}")
c2.metric("Nakamoto Coefficient", nakamoto_coeffecient)
c3.metric("Gini Coefficient", f"{gini_coeffecient:.3f}")

with st.expander("Defintions"):
    st.write(
        """
    - Nakamoto Coefficient: the minimum number of validators needed to control 33.3%% of the total staked NEAR and halt the network
    - Gini Coefficient: a metric to quantify income inequality, see [here](https://github.com/oliviaguest/gini) for calculations and information
    """
    )
st.subheader("The Governors")
"""
Information about the NEAR Governors (the active validator set) below.
Choose how what you would like to look at (such as amount of NEAR staked), and how many Governors you would like to see in the chart, in ranked order.
"""
flipside_data = load_data()
validator_activity = flipside_data["validator_activity"]
stakers = flipside_data["stakers"]

tmp_df = pd.merge(
    vals_sorted_stake, validator_activity, left_on="account_id", right_on="BLOCK_AUTHOR"
)
all_val_data = pd.merge(tmp_df, stakers, left_on="account_id", right_on="GOVERNOR")
c1, c2 = st.columns([1, 3])
value = c1.selectbox(
    "Which variable?",
    list(validator_column_mappings.keys())[1:],  # HACK: remove the X value
    format_func=lambda x: validator_column_mappings[x]["title"],
    key="val_overview",
)
n_validators = c2.slider(
    "How many Governors?", 1, len(validator_names), (0, 25), key="val_overview"
)
st.altair_chart(
    alt_rank_bar(
        all_val_data, value, n_validators, validator_column_mappings
    ).properties(height=500),
    use_container_width=True,
)
if value == "reward_fee":
    st.caption(
        "NOTE: this variable (`Reward Fee (%)`)often returns a lot of NA values, so this may be inaccurate"
    )

st.header("My representative")
"""
Governments have many members, but sometimes we only care about the representatives for our home region.

Lets inspect how our favorite governor has fared over time. 
"""
validator = st.selectbox("Choose an active validator", validator_names)
load_fs_msg = st.text("Loading data from Flipside Crypto...")
try:
    df = get_fs_validator_data(validator, cached=True)
except errors.UserError:
    df = get_fs_validator_data(validator, cached=False)

st.subheader("Year to date record")
"""We can see our Governor's daily stats since 2022-01-01, and examine the total staked balance, number of blocks produced, and number of transactions processed in those blocks for each day."""
var = st.selectbox(
    "Choose which variable to look at:", [ "Transactions Processed", "Blocks produced",]
)
st.altair_chart(
    alt_lines_bar(df, validator, value_vars=[var]).properties(height=500),
    use_container_width=True,
)
load_fs_msg.text("")

st.subheader("Results by Epoch")
"""
Additionally, let's take a look at a more completed voting record: how our Governor performed during each epoch where it produced blocks. We can see the number of blocks produced, and NEAR balance.
"""
validator_epochs = get_validator_epochs(validator)
st.altair_chart(
    alt_lines_bar(
        validator_epochs,
        validator,
        date_col="last_time",
        variable_col="Staking Balance (NEAR)",
        value_vars=["produced_blocks"],
        date_type=("yearmonthdatehours"),
    ).properties(height=500),
    use_container_width=True,
)


st.header("Methods")
f"""
Data was acquired from Flipside Crypto's NEAR tables, as well as [Figment's Enriched APIs](https://docs.figment.io/network-documentation/near/enriched-apis) for more real time information.

Governance queries were adopted from [excellent work](https://app.flipsidecrypto.com/dashboard/citizens-of-near-THIJUc) done on previous bounties by [@darksoulsfanlol](https://twitter.com/darksoulsfanlol).

The "Year to date record" secion uses Flipside data, while other sections use Figment's API.

All code is available on github, with the interactive validator query in the "My representative" section available [here](https://github.com/ltirrell/flipside_bounties/blob/main/near/gov_utils.py#L278).

Other queries are hosted on Flipside Crytpo here:
"""
for k, v in query_information.items():
    x = f"- [{k}]({v['query']})"
    x


# TODO: look to add this in:
# account_info = get_account_info("ltirrell.near")
# "blocks"
# blocks
# "epochs"
# epochs
# "validator_epochs"
# validator_epochs
# "account_info"
# account_info
