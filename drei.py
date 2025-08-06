import os
import time
import pandas as pd
import sys
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from datetime import datetime, date
import drei_func as drf ##functions stored externally
import drei_prompt as drp ##prompts stored externally

## load the API key from .env
load_dotenv()

## set AI models and prompt types
get_ai = input("(G)emini or (O)penAI? ").upper()
model = input("Please enter the name of the model: ")
prompt_code = input("(U)nguided, (D)efined, (F)ull prompt? ").upper()
prompt_name = prompt_code

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
        print("excel file is missing: python drei.py <path_to_excel>")
        sys.exit(1)

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

    ##create a subfolder to store the results
    subfolder = f"results_{date.today()}"
    try:
        os.mkdir(subfolder)
    except FileExistsError:
        print("Subfolder exists already.")

    ##extract a list of csv transcripts
    input_file = sys.argv[1]
    main = pd.read_excel(input_file)
    file_list = main['names']
    ##batch process the transcripts
    for csv in file_list:
        if os.path.exists(csv): ##continue if the file can be found
            df = pd.read_csv(csv)
            ##create an output file and rename it if it already exists
            output_csv = f"{csv[0:-4]}_prompt={prompt_name}_{model}.csv"
            if os.path.exists(f"./{subfolder}/{output_csv}"):
                i = 1
                while True:
                    new_output_csv = f"{output_csv[0:-4]}_{i}.csv"
                    if not os.path.exists(new_output_csv):
                        output_csv = new_output_csv
                        break
                    i += 1

            dialogue_col = drf.select_dialogue_column(df) ##this uses function 2.1
            speaker_col = drf.select_speaker_column(df) ##this uses function 2.2
            #print(f"使用欄位作為逐字稿：{dialogue_col}") ##too verbose: name of speech column

            batch_size = 10
            total = len(df)
            print(f"\nProcessing {csv}...")
            print(f"\n***THE STOPWATCH HAS STARTED*** \nTotal number of sentencces to process: {total}")
            datetime1 = datetime.now() ##Get start time

            for start_idx in range(0, total, batch_size):
                end_idx = min(start_idx + batch_size, total)
                batch = df.iloc[start_idx:end_idx]
                dialogues = batch[dialogue_col].tolist()
                dialogues = [str(d).strip() for d in dialogues]
                speakers = batch[speaker_col].tolist()
                speakers = [str(d).strip() for d in speakers]
                batch_results = drp.process_batch_dialogue(client, speakers, dialogues, ITEMS=ITEMS,
                                                        prompt_code=prompt_code, get_ai=get_ai, model=model) ##this uses function 4 (which uses function 1)
                batch_df = batch.copy()
                for item in ITEMS:
                    batch_df[item] = [res.get(item, "") for res in batch_results]
                if start_idx == 0:
                    batch_df.to_csv(f"./{subfolder}/{output_csv}", index=False, encoding="utf-8-sig")
                else:
                    batch_df.to_csv(f"./{subfolder}/{output_csv}", mode='a', index=False, header=False, encoding="utf-8-sig")
                print(f"Processing {end_idx} / {total}")
                time.sleep(1)

            print(f"\n***THE STOPWATCH HAS STOPPED*** \n\nThe output is stored as {output_csv}.")

            ##Calculate the duration taken
            datetime2 = datetime.now() ##Get end time
            drf.get_time_diff(datetime1=datetime1, datetime2=datetime2, model=model, total=total)

    print(f"All {len(file_list)} files have been processed.\n")

if __name__ == "__main__":
    main()
