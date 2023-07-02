from naturalmaps_bot import ChatBot
import os
import pandas as pd


prompts = pd.read_csv("../prompts/prompts.csv")
print(prompts.head())
