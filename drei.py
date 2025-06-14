import os
import json
import time
import pandas as pd
import sys
from dotenv import load_dotenv
from docx import Document
from google import genai
from google.genai.errors import ServerError
from openai import OpenAI
from datetime import datetime

# load the API key from .env
load_dotenv()

# set AI models and prompt types
get_ai = input("(G)emini or (O)penAI? ").upper()
model = input("Please enter the name of the model: ")
prompt_code = input("(U)nguided, (D)efined, or (F)ull prompt? ").upper()
if prompt_code == "D" or prompt_code == "F":
    prompt_name = prompt_code
else:
    prompt_name = "U"

# coding criteria
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

def parse_response(response_text): ##function 1: parse response
    """
    嘗試解析 Gemini API 回傳的 JSON 格式結果。
    如果回傳內容被 markdown 的反引號包圍，則先移除這些標記。
    若解析失敗，則回傳所有項目皆為空的字典。
    """
    cleaned = response_text.strip()
    # 如果回傳內容以三個反引號開始，則移除第一行和最後一行
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        result = json.loads(cleaned)
        for item in ITEMS:
            if item not in result:
                result[item] = ""
        return result
    except Exception as e:
        #print(f"Failed to parse JSON： {e}")
        #print(response_text)
        return {item: "" for item in ITEMS}

def select_dialogue_column(chunk: pd.DataFrame) -> str: ##function 2.1: select utterance column
    """
    根據 CSV 欄位內容自動選取存放逐字稿的欄位。
    優先檢查常見欄位名稱："text", "utterance", "content", "dialogue"
    若都不存在，則回傳第一個欄位。
    """
    preferred = ["text", "utterance", "content", "dialogue"]
    for col in preferred:
        if col in chunk.columns:
            return col
    print("CSV column： ", list(chunk.columns))
    return chunk.columns[0]

def select_speaker_column(chunk: pd.DataFrame) -> str: ##function 2.2: select speaker column
    """
    根據 CSV 欄位內容自動選取存放逐字稿的欄位。
    優先檢查常見欄位名稱
    若都不存在，則回傳第一個欄位。
    """
    preferred = ["who", "speaker", "dyad"]
    for col in preferred:
        if col in chunk.columns:
            return col
    return chunk.columns[0]

def get_definitions(docx_path): ##function 3: get definitions
    """
    script written by ChatGPT
    讀取評分標準 Word 文件
    """
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def process_batch_dialogue(client, dialogues: list, delimiter="-----"): ##function 4: process dialogues
    """
    將多筆逐字稿合併成一個批次請求。
    提示中要求模型對每筆逐字稿產生 JSON 格式回覆，
    並以指定的 delimiter 分隔各筆結果。
    """
    ##General instructions that apply across the board regardless of how the coding scheme is defined.
    ##updated_0613
    gen_inst_1 = (
        "你是一位親子對話分析專家，請根據以下規則編碼家長唸故事書時的每一句話，\n"
        + "\n".join(ITEMS)+ "\n"
    )
    gen_inst_2 = (
        "\n\n若觸及多個編碼規則，completion, recall, open-ended, wh, distancing 可重複標記為1。但是evaluate, expand, repeat只能擇一。"
        "speaker裡MOT為媽媽, FAT為爸爸, CHI為小孩, 若 speaker 不是媽媽或爸爸，則不編碼。" ##this uses function 2.2
        "若句子和上一句相同，則不編碼。"
        "請在Notes裡簡單說明編碼原因。\n"
        "請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "{\n  \"Prompt\": \"1\",\n  \"Evaluate\": \"\",\n  ...\n}\n"
        f"{delimiter}\n"
        "{{...}}\n```"
    )

    ##Provide simple definitions with an example or two to illustrate.
    ##definition_0613
    definition = (
        "evaluate是針對若上一句為孩子說出來的內容給予肯定、修正或以完整句子再說一次, "
        "expand是針對若上一句為孩子說出來的內容去增加新訊息加以延伸,"
        "repeat是家長請孩子複述家長說過的話 ，而非家長重複說話, 例: 你說馬,"
        "completion是利用語句停頓，等待孩子完成句子,"
        "open-end是無固定答案的問句, 例: 小金魚為什麼要一直逃走呢？,"
        "wh是人事時地物問句 (例: 這是什麼？馬怎麼叫？), 不包含是非問題 (例: 看看這是什麼好不好) 或模糊問句 (例: 在哪裡？) ,"
        "distancing是將書中情節與幼兒生活經驗做連結。"
   )

    ##Provide the entire coding scheme document.
    full = (
        "請用文件的定義: " + get_definitions("peer.docx") ##this uses function 3
   )

    prompt_unguided = gen_inst_1 + gen_inst_2 ##no extra definitions provided!
    prompt_definition = gen_inst_1 + definition + gen_inst_2
    prompt_full = gen_inst_1 + full + gen_inst_2

    if prompt_code == "D":
        get_prompt = prompt_definition
    elif prompt_code == "F":
        get_prompt = prompt_full
    else:
        get_prompt = prompt_unguided

    batch_text = f"\n{delimiter}\n".join(dialogues)
    content = get_prompt + "\n\n" + batch_text

    try:
        if get_ai == "G":
            response = client.models.generate_content(
                model = model,
                # temperature=0,
                contents = content
            )
        elif get_ai == "O":
            response = client.responses.create(
                model = model,
                # temperature=0,
                input=[
                    {
                        "role": "user",
                        "content": content
                        }
                ]
            )
    except ServerError as e:
        print(f"Failed to call API：{e}")
        return [{item: "" for item in ITEMS} for _ in dialogues]

    # print("AI is working： ", response.text) ##too verbose: which utterance is being processed
    if get_ai == "G":
        parts = response.text.split(delimiter)
    elif get_ai == "O":
        parts = response.output_text.split(delimiter)
    results = []
    for part in parts:
        part = part.strip()
        if part:
            results.append(parse_response(part)) ##this uses function 1
    # 若結果數量多於原始筆數，僅取前面對應筆數；若不足則補足空結果
    if len(results) > len(dialogues):
        results = results[:len(dialogues)]
    elif len(results) < len(dialogues):
        results.extend([{item: "" for item in ITEMS}] * (len(dialogues) - len(results)))
    return results

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

    dialogue_col = select_dialogue_column(df) ##this uses function 2.1
    #print(f"使用欄位作為逐字稿：{dialogue_col}") ##too verbose: name of speech column
    
    speaker_col = select_speaker_column(df) ##this uses function 2.2

    batch_size = 10
    total = len(df)
    print(f"\n***THE STOPWATCH HAS STARTED*** \nTotal number of sentencces to process: {total}")
    datetime1 = datetime.now() ##Get start time

    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]
        dialogues = batch[dialogue_col].tolist()
        dialogues = [str(d).strip() for d in dialogues]
        batch_results = process_batch_dialogue(client, dialogues) ##this uses function 4 (which uses function 1)
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
        print("More than an hour! ")
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
