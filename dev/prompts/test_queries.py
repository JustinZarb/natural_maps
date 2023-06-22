from openai_function_calls import run_prompt
import pandas as pd

prompts = pd.read_csv("prompts.csv")
basic_prompts = prompts.loc[prompts.loc[:, "promptType"] == "Basic Query", "prompt"]

for test_prompt in basic_prompts[:1]:
    print(test_prompt)
    run_prompt(test_prompt)
