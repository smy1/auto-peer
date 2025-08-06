'''
Three functions that extract relevant information from the input csv file
for the AI model to process.
Written by Prof Pecu Tsai, March 2025
Stored as an external function by MY Sia, June 2025
'''
import json
import pandas as pd

def parse_response(response_text, ITEMS): ##function 1: parse response
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
    preferred = ["who", "speaker", "Speaker"]
    for col in preferred:
        if col in chunk.columns:
            return col
    return chunk.columns[0]

def get_time_diff(datetime1, datetime2, model, total):
    """
    Calculate the time needed for AI to process one transcript
    """
    difftime = datetime2-datetime1
    difftime = difftime.total_seconds()
    if difftime >= 60:
        diffmin = difftime//60
        diffsec = difftime%60
    else:
        diffmin = 0
        diffsec = difftime
    print(f"{model} took {diffmin} minute(s) and {round(diffsec, 2)} second(s) to process {total} sentences.\n")

