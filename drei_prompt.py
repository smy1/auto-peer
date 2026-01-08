'''
Two functions that give instructions (prompts) to the AI model,
so that it knows how to process the input csv file.
Written by Prof Pecu Tsai, March 2025
Edited and stored as an external function by MY Sia, July 2025
Details of the prompts are modified jointly by Prof S Wang, MY Sia, & YY Chen, June 2025
'''
from google.genai.errors import ServerError
from docx import Document
import drei_func as drf ##functions stored externally

def get_definitions(docx_path):
    """
    script written by ChatGPT
    讀取評分標準 Word 文件
    """
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def process_batch_dialogue(client, speakers: list, dialogues: list, ITEMS, prompt_code, get_ai, model, delimiter="-----"):
    """
    將多筆逐字稿合併成一個批次請求。
    提示中要求模型對每筆逐字稿產生 JSON 格式回覆，
    並以指定的 delimiter 分隔各筆結果。
    """
    ##General instructions that apply across the board regardless of how the coding scheme is defined.
    ##up-to-date_20251229
    gen_inst_1 = (
        "你是一位親子對話分析專家，請根據以下規則編碼家長唸故事書時的每一句話，\n"
        + "\n".join(ITEMS)+ "\n"
    )
    gen_inst_2 = (
        "\n\n若觸及多個編碼規則，completion, recall, open-ended, wh, distancing 可重複標記為1。但是evaluate, expand, repeat只能擇一。"
        "speaker裡MOT為媽媽, FAT為爸爸, CHI為小孩, 若 speaker 不是媽媽或爸爸，則在Notes裡說明，並無需編碼句子。"
        "若句子為疑問句且上一句speaker為CHI，且觸及evaluate或expand編碼規則，則優先將evaluate或expand標記為1。"
        "若句子和上一句相同，則不編碼。"
        "請在Notes裡以繁體中文簡單說明編碼原因。\n"
        "請對每筆逐字稿產生 JSON 格式回覆，並在各筆結果間用下列分隔線隔開：\n"
        f"{delimiter}\n"
        "例如：\n"
        "{\n  \"Prompt\": \"1\",\n  \"Evaluate\": \"\",\n  ...\n}\n"
        f"{delimiter}\n"
        "{{...}}\n```"
    )

    ##Provide simple definitions with an example or two to illustrate
    ##up-to-date_20250613
    definition = (
        "evaluate是針對若上一句為孩子說出來的內容給予肯定、修正或以完整句子再說一次, "
        "expand是針對若上一句為孩子說出來的內容去增加新訊息加以延伸,"
        "repeat是家長請孩子複述家長說過的話 ，而非家長重複說話 (例: 你說馬),"
        "completion是利用語句停頓，等待孩子完成句子,"
        "open-end是無固定答案的問句, 例: 小金魚為什麼要一直逃走呢？,"
        "wh是人事時地物問句 (例: 這是什麼？馬怎麼叫？), 不包含是非問題 (例: 看看這是什麼好不好) 或模糊問句 (例: 在哪裡？) ,"
        "distancing是將書中情節與幼兒生活經驗做連結。\n"
        "請在Notes裡簡單說明編碼原因。\n"
   )

    ##Provide the entire coding scheme document
    full = (
        "請用文件的定義: " + get_definitions("peer_full.docx")
   )

    prompt_unguided = gen_inst_1 + gen_inst_2 ##no extra definitions provided!
    prompt_definition = gen_inst_1 + definition + gen_inst_2
    prompt_full = gen_inst_1 + full + gen_inst_2

    if prompt_code == "D":
        get_prompt = prompt_definition
    elif prompt_code == "F":
        get_prompt = prompt_full
    elif prompt_code == "U":
        get_prompt = prompt_unguided

    ##Combine the speaker and dialogue into a formatted string (OpenAI)
    # batch_text = f"\n{delimiter}\n".join(dialogues) ##(original from Prof Tsai)
    batch_text = "\n".join(f"{speakers[i]}: {dialogues[i]}" for i in range(len(dialogues)))
    batch_text = f"\n{delimiter}\n".join(batch_text.split('\n'))
    # print(batch_text)
    content = get_prompt + "\n\n" + batch_text

    try:
        if get_ai == "G":
            response = client.models.generate_content(
                model = model,
                contents = content
            )
        elif get_ai == "O":
            response = client.responses.create(
                model = model,
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
            results.append(drf.parse_response(part, ITEMS=ITEMS)) ##this uses function 1
    # 若結果數量多於原始筆數，僅取前面對應筆數；若不足則補足空結果
    if len(results) > len(dialogues):
        results = results[:len(dialogues)]
    elif len(results) < len(dialogues):
        results.extend([{item: "" for item in ITEMS}] * (len(dialogues) - len(results)))
    return results
