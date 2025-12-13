'''
This script reads a coded csv file and a word document that contains the coding scheme
and then calls an OpenAI model to generate points on the parent's positive behaviour, lacking strategies, and suggestions.
These points are then produced as a pdf output.
Written by MY Sia, Nov 2025
'''
print("Getting ready...")

import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date
import pandas as pd
from docx import Document
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm ##to print in Chinese
##to create a pdf
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

## load the API key from .env
load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

xfile=input("Please enter the full name of the csv file (e.g., 099_coded.csv): ")
if xfile[-4:] != ".csv":
    xfile=f"{xfile}.csv"

age=str(input("Please enter the child's age in years, in Arabic number (e.g., 1): "))
model=input("Please enter the name of the model (e.g., gpt-5.1): ")

## Step 1: Feed info
def get_definitions(docx_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

## Step 2: Create the main text
def gen_summary(age, csv, task, model):
    df = pd.read_csv(csv)
    client = OpenAI(api_key=openai_api_key)

    ##prepare the prompts
    gen_inst_1 = f"""
    You are a child psychologist who specialises in dialogic reading (DR).
    Here is a coded transcript between a parent and a {age}-year-old child: {df}.
    It has already been coded using this DR coding scheme: {get_definitions("peer_20250725_full.docx")}.
    """
    gen_positive = f"""
    Your task is to identify 2-3 positive reading behaviour in the transcript.
    Please provide an example sentence from the transcript to briefly support your point.
    A summary or conclusion is not needed.
    """
    gen_lacking = f"""
    Your task is to identify 2-3 DR strategies that the parent did not or rarely used.
    The identified strategy should be appropriate for the verbal ability of a typical {age}-year-old child.
    Do not give any advice and suggestions. A summary or conclusion is not needed.
    """
    gen_suggest = f"""
    Your task is to highlight 2-3 DR strategies that the parent could have used with the child, but did not.
    The suggested strategies must be appropriate for the verbal ability of a typical {age}-year-old child.
    You may also provide encouragements as a brief concluding remark.
    """
    gen_inst_2 = f"""
    Please add <br /><br /> between your main points.
    Please write the review in a polite, parent-friendly manner, using traditional Chinese characters.
    You must keep the review within 400 words.
    """

    ##choose the prompt based on the task
    if task == "positive":
        prompt = gen_inst_1 + gen_positive + gen_inst_2
    elif task == "lacking":
        prompt = gen_inst_1 + gen_lacking + gen_inst_2
    elif task == "suggestion":
        prompt = gen_inst_1 + gen_suggest + gen_inst_2

    ##
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user",
             "content": prompt}
        ]
    )
    return response.choices[0].message.content


## Step 3: Plot the graph
def create_chart(csv, filename="bar.png"):
    ##calculate the scores
    df = pd.read_csv(csv)
    ##subset all DR data
    justdr=df[['Evaluate', 'Expand', 'Repeat', 'Completion', 'Recall', 'Open-end', 'Wh', 'Distancing']]
    justdr=justdr.apply(pd.to_numeric, errors='coerce')
    sumscore=justdr.sum() ##sum every column
    Prompt=sum(sumscore[3:8]) ##prompt score is the total of crowd
    PEER=sum(sumscore)
    sumscore['Prompt']=Prompt
    sumscore['PEER']=PEER
    ##rearrange the variables
    desired_order = ['PEER', 'Prompt', 'Evaluate', 'Expand', 'Repeat', 'Open-end', 'Completion', 'Recall', 'Wh', 'Distancing']
    sumscore = sumscore[desired_order]

    ##create a simple bar chart
    categories = list(sumscore.index) ##these are the keys (column names)
    values = list(sumscore.values) ##these are the values (sum of each column)
    ##adjust plotting regions
    chinese_font = fm.FontProperties(fname='ChironGoRoundTC-Regular.ttf')
    custom_labels = ['總分','引','評','論','述','放','空','想','人','生']
    plt.subplots_adjust(left=0.1, right=0.95, bottom=0.18, top=0.95)
    plt.bar(categories, values, color='skyblue')
    plt.title("親子共讀時所使用的策略頻率", fontproperties=chinese_font)
    plt.xlabel("共讀策略", fontproperties=chinese_font)
    plt.ylabel("使用頻率", fontproperties=chinese_font)
    plt.xticks(categories, custom_labels, fontproperties=chinese_font)
    # plt.xticks(rotation=25, ha='right') ##rotate category labels for better visibility
    ##save as PNG
    plt.savefig(filename, format="png")
    plt.close()

## Step 4: Export text as pdf
def save_pdf(age, chart_name, POS_BEHAVIOUR, WHAT_LACKS, SUGGESTIONS, filename="output.pdf"):
    ##create the PDF object
    pdf = SimpleDocTemplate(filename, pagesize=A4, topMargin=40, bottomMargin=40, leftMargin=60, rightMargin=60)
    story = []

    ##add Traditional Chinese
    pdfmetrics.registerFont(TTFont('NotoSans', 'ChironGoRoundTC-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('NotoSans-Bold', 'ChironGoRoundTC-SemiBold.ttf'))
    styles = getSampleStyleSheet()

    ##create heading 1 style
    head1_style = styles['Heading1']
    head1_style.fontName = 'NotoSans-Bold'
    head1_style.fontSize = 20
    head1_style.alignment = 1 ##centered

    ##create heading 2 style
    head2_style = styles['Heading2']
    head2_style.fontName = 'NotoSans-Bold'
    head2_style.fontSize = 18
    head2_style.spaceBefore = 20

    ##create a normal style
    style = styles['Normal']
    style.fontName = 'NotoSans'
    style.fontSize = 14
    style.leading = 18
    style.spaceAfter = 10

    ##create the doc
    text_title = Paragraph("<b>親子對話式共讀回饋報告書</b>", head1_style)
    story.append(text_title)

    text_intro=f"""本報告依據您與{age}歲孩子在親子共讀逐字稿與對話式共讀編碼結果所撰寫，
目的在協助您了解自己在共讀時所使用的策略類型、頻率，以及如何透過調整互動方式，提升孩子的語言與認知發展。本報告分為四大部分：
"""
    text = Paragraph(text_intro, style=style)
    story.append(text)
    ##create a numbered list
    numbered_list = [
        "對話式共讀簡介",
        "策略使用統計",
        "行為與互動質量分析",
        "未來共讀練習方向"
    ]
    ##create a ListFlowable for the numbered list
    list_items = []
    for item in numbered_list:
        list_item = ListItem(Paragraph(item, styles['Normal']))
        list_items.append(list_item)

    numbered_list_flowable = ListFlowable(list_items, bulletType='1', start='1')
    story.append(numbered_list_flowable)

    ##PART1
    text_title = Paragraph("<b>1. 什麼是對話式共讀?</b>", head2_style)
    story.append(text_title)

    text_body="""對話式共讀是一種在親子共讀過程中與兒童互動的方法。它可以用以下的策略來記住：”引評論述”和”放空想人生”。
”引評論述”代表“引導“(引導孩子談論書本內容)，“評估“(提供正確答案或修正孩子的答案)，“延伸討論“(根據孩子的回應，做進一步相關討論)，和“複述“(請孩子重複一次正確答案)。
”放空想人生”代表五個有效的引導：” 開放式問題”， ” 填空”， ” 回想”， ” 人事時地物”， ” 連結生活經驗”。
透過引導和複述，家長可以鼓勵孩子發言，也可以透過評估和延伸討論並為他們提供適時的回饋。
"""
    text = Paragraph(text_body, style=style)
    story.append(text)

    ##PART2
    text_title = Paragraph("<b>2. 策略使用統計</b>", head2_style)
    story.append(text_title)

    text_body="下圖統整本次共讀中”引評論述”和”放空想人生”策略之使用次數："
    text = Paragraph(text_body, style)
    story.append(text)
    ##add chart
    img = Image(chart_name, width=500, height=300)
    story.append(img)

    ##PART3
    text_title = Paragraph("<b>3. 行為與互動質量分析</b>", head2_style)
    story.append(text_title)
    text = Paragraph("根據逐字稿內容與策略使用頻率，整體呈現出以下特徵： <br /> 【優勢亮點】", style)
    story.append(text)
    text = Paragraph(POS_BEHAVIOUR, style=style)
    story.append(text)
    text = Paragraph("【可深化之互動模式】", style)
    story.append(text)
    text = Paragraph(WHAT_LACKS, style=style)
    story.append(text)

    ##PART4
    text_title = Paragraph("<b>4. 未來共讀練習方向</b>", head2_style)
    story.append(text_title)
    text = Paragraph(SUGGESTIONS, style=style)
    story.append(text)

    ##pass the content to the pdf object
    pdf.build(story)
    print(f"PDF saved as: {filename}")


## Example usage:
if __name__ == "__main__":
    # xfile="099_F_o4-mini_250728_1.csv"
    # age="1"
    # model="gpt-5.1"
    create_chart(xfile)
    POS_BEHAVIOUR = gen_summary(age, xfile, "positive", model)
    WHAT_LACKS = gen_summary(age, xfile, "lacking", model)
    SUGGESTIONS = gen_summary(age, xfile, "suggestion", model)
    save_pdf(age, "bar.png", POS_BEHAVIOUR, WHAT_LACKS, SUGGESTIONS, f"sbr-report_{xfile[:-4]}_age{age}y_{date.today()}.pdf")
