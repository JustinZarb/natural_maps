import streamlit as st
import os
import pandas as pd

st.title("Benchmarks")


"""
# For some weird reason this doesnt work
prompts = pd.read_csv(r"../dev/prompts/prompts.csv")
st.table(prompts)"""

st.markdown(
    "Check [Github](https://github.com/JustinZarb/shade-calculator/tree/main/dev/prompts)"
)
