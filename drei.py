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

# load the API key from .env
load_dotenv()

get_ai = "openai" #"gemini" or "openai"
model = "gpt-4o-mini"

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
    prompt_unguided = (
        "你是一位親子對話分析專家，請根據以下編碼規則評估家長(speaker里mot為妈妈，fat為爸爸)唸故事書時的每一句話，\n"
        + "\n".join(ITEMS) +
        "\n\n請依據評估結果，對每個項目：若觸及則標記為 1，否則留空。若觸及多個編碼評估, 請選一個標記為 1。"
        "若 speaker 不是 mot 或 fat(如chi是小孩)，請不要評估那句話。" ##this uses function 2.2
        "請在 Notes 里简单说明評估原因。"
        " 請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "{\n  \"Prompt\": \"1\",\n  \"Evaluate\": \"\",\n  ...\n}\n"
        f"{delimiter}\n"
        "{{...}}\n```"
    )

    prompt_definition = (
        "你是一位親子對話分析專家，請根據以下編碼規則評估家長(speaker里mot為妈妈，fat為爸爸)唸故事書時的每一句話，\n"
        + "\n".join(ITEMS) +
        "evaluate是對孩子給予回應、回饋、鼓勵或修正,"
        "expand是將孩子說出來的內容加以延伸重組,"
        "repeat是鼓勵並引導孩子說答案，而非家長重複說話, 例:你說馬,"
        "completion是將句尾詞彙或語句空白，等待孩子用口語補上句尾詞彙,"
        "open-end是無固定答案的問句, 例:小金魚為什麼要一直逃走呢？,"
        "wh是人事時地物問句, 例:這是什麼？馬怎麼叫？。 不包含是非問題, 例: 你有看到吗？,"
        "distancing是協助兒童將書中部分情節與自身生活經驗做連結。"
        "\n\n請依據評估結果，對每個項目： 若觸及則標記為 1，否則留空。 若觸及多個編碼評估, 請選一個標記為 1。"
        "若 speaker 不是 mot 或 fat(如chi是小孩)，請不要評估那句話。" ##this uses function 2.2
        "請在 Notes 里简单说明評估原因。\n"
        " 請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "{\n  \"Prompt\": \"1\",\n  \"Evaluate\": \"\",\n  ...\n}\n"
        f"{delimiter}\n"
        "{{...}}\n```"
   )

    prompt_full = (
        "你是一位親子對話分析專家，請根據以下編碼規則評估家長(speaker里mot為妈妈，fat為爸爸)唸故事書時的每一句話，\n"
        + "\n".join(ITEMS) +
        "請用文件的定義: "+ get_definitions("peer.docx") + ##this uses function 3
        "\n\n請依據評估結果，對每個項目： 若觸及則標記為 1，否則留空。 若觸及多個編碼評估, 請選一個標記為 1。"
        "若 speaker 不是 mot 或 fat(如chi是小孩)，請不要評估那句話。" ##this uses function 2.2
        "請在 Notes 里简单说明評估原因。"
        " 請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "{\n  \"Prompt\": \"1\",\n  \"Evaluate\": \"\",\n  ...\n}\n"
        f"{delimiter}\n"
        "{{...}}\n```"
   )

    batch_text = f"\n{delimiter}\n".join(dialogues)
    content = prompt_definition + "\n\n" + batch_text

    try:
        if get_ai == "gemini":
            response = client.models.generate_content(
                model = model,
                # temperature=0,
                contents = content
            )
        elif get_ai == "openai":
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
    if get_ai == "gemini":
        parts = response.text.split(delimiter)
    elif get_ai == "openai":
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
    print("Loading and processing...")
    # get_prompt = input("prompt_unguided, prompt_definition, or prompt_full? ")
    # get_ai = input("gemini or openai? ") #!!!WHY IS THIS NOT ACCESSED??

    if len(sys.argv) < 2:
        print("csv file is missing: python drei.py <path_to_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = f"{input_csv[0:-4]}_prompt=D_{model}.csv"
    print("Using a definition-provided prompt...")

    if os.path.exists(output_csv):
        output_csv = f"{output_csv[0:-4]}_(1).csv"
        # os.remove(output_csv)
    
    df = pd.read_csv(input_csv)

    ##choose AI model and API key
    if get_ai == "gemini":
        print("Reading GEMINI API key...")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            gemini_api_key = input("Enter your GEMINI API key: ")
        client = genai.Client(api_key=gemini_api_key)
    elif get_ai == "openai":
        print("Reading OPENAI API key...")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = input("Enter your OPENAI API key: ")
        client = OpenAI(api_key=openai_api_key)

    dialogue_col = select_dialogue_column(df) ##this uses function 2.1
    #print(f"使用欄位作為逐字稿：{dialogue_col}") ##too verbose: name of speech column
    
    speaker_col = select_speaker_column(df) ##this uses function 2.2

    batch_size = 10
    total = len(df)
    print(f"Total number of sentencces to process: {total}")
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
    print("All processing is completed. The output is stored in ", output_csv)

if __name__ == "__main__":
    main()
