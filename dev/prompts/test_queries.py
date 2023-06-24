from dev.prompts.naturalmaps_function import run_prompt  # change to naturalmaps_bot
import pandas as pd

prompts = pd.read_csv("prompts.csv")
basic_prompts = prompts.loc[prompts.loc[:, "promptType"] == "Basic Query", "prompt"]

for test_prompt in basic_prompts[:1]:
    print(test_prompt)
    run_prompt(test_prompt)
