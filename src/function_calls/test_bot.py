import pandas as pd
import os


def get_test_prompts(prompt_type=None):
    prompts = pd.read_csv("./dev//prompts/prompts.csv")
    prompt_type = prompts.promptType.unique()
    if prompt_type is not None:
        return prompts.loc[prompts.loc[:, "promptType"] == prompt_type, "prompt"]
    else:
        return prompts
