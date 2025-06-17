import os
import time
import pandas as pd
import sys
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from datetime import datetime
import drei_func as drf ##functions stored externally
import drei_prompt as drp ##prompts stored externally

## load the API key from .env
load_dotenv()

## set AI models and prompt types
get_ai = input("(G)emini or (O)penAI? ").upper()
model = input("Please enter the name of the model: ")
prompt_code = input("(U)nguided, (D)efined, or (F)ull prompt? ").upper()
if prompt_code == "D" or prompt_code == "F":
    prompt_name = prompt_code
else:
    prompt_name = "U"

## coding criteria
ITEMS = [
    #"Prompt",
    "Evaluate",
    #"Evaluate.nonverbal",
    "Expand",
    "Repeat",
    "Completion",
    "Recall",
    "Open-end",
    "Wh",
    "Distancing",
    "Notes"
]

def main():
    if len(sys.argv) < 2:
        print("csv file is missing: python drei.py <path_to_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = f"{input_csv[0:-4]}_prompt={prompt_name}_{model}.csv"
    if os.path.exists(output_csv):
        i = 1
        while True:
            new_output_csv = f"{output_csv[0:-4]}_{i}.csv"
            if not os.path.exists(new_output_csv):
                output_csv = new_output_csv
                break
            i += 1
    df = pd.read_csv(input_csv)

    ##choose AI model and API key
    if get_ai == "G":
        print("Reading GEMINI API key...")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            gemini_api_key = input("Enter your GEMINI API key: ")
        client = genai.Client(api_key=gemini_api_key)
    elif get_ai == "O":
        print("Reading OPENAI API key...")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = input("Enter your OPENAI API key: ")
        client = OpenAI(api_key=openai_api_key)

    print(f"Getting the ({prompt_name}) prompt...")

    dialogue_col = drf.select_dialogue_column(df) ##this uses function 2.1
    #print(f"使用欄位作為逐字稿：{dialogue_col}") ##too verbose: name of speech column
    
    speaker_col = drf.select_speaker_column(df) ##this uses function 2.2

    batch_size = 10
    total = len(df)
    print(f"\n***THE STOPWATCH HAS STARTED*** \nTotal number of sentencces to process: {total}")
    datetime1 = datetime.now() ##Get start time

    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        dialogues = batch[dialogue_col].tolist()
        dialogues = [str(d).strip() for d in dialogues]
        batch_results = drp.process_batch_dialogue(client, dialogues, ITEMS=ITEMS,
                                                   prompt_code=prompt_code, get_ai=get_ai, model=model) ##this uses function 4 (which uses function 1)
        batch_df = batch.copy()
        for item in ITEMS:
            batch_df[item] = [res.get(item, "") for res in batch_results]
        if start_idx == 0:
            batch_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        else:
            batch_df.to_csv(output_csv, mode='a', index=False, header=False, encoding="utf-8-sig")
        print(f"Processing {end_idx} / {total}")
        time.sleep(1)

    print(f"All processing is completed. \n***THE STOPWATCH HAS STOPPED*** \n\nThe output is stored as {output_csv}.")
    ##Calculate the duration taken
    datetime2 = datetime.now() ##Get end time
    difftime = datetime2-datetime1
    difftime = difftime.total_seconds()
    if difftime > 3599:
        print("More than an hour!")
        diffmin = "at least 60"
        diffsec = "xx"
    elif difftime >= 60:
        diffmin = difftime//60
        diffsec = difftime%60
    else:
        diffmin = 0
        diffsec = difftime
    print(f"{model} took {diffmin} minute(s) and {round(diffsec, 2)} second(s) to process {total} sentences.\n")

if __name__ == "__main__":
    main()
