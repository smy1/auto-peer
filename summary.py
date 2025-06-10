import glob
from pathlib import Path
import pandas as pd
# import os

## create an empty DataFrame
df = pd.DataFrame()
df['ID']=[]
df['model']=[]
df['PEER']=[]
df['prompt']=[]
df['evaluate']=[]
df['expand']=[]
df['repeat']=[]
df['completion']=[]
df['recall']=[]
df['openend']=[]
df['wh']=[]
df['distancing']=[]

##locate csv files
proj = "C:/Users/user/Desktop/smy/PROJECTS/DREI"
files_path = Path(f"{proj}")
file_list = glob.glob(f"{files_path}/*.csv")

##loop csv files
for csv_file in file_list:
    csv=pd.read_csv(csv_file)
    kid=csv_file[len(proj)+1:len(proj)+4] ##ID of child
    model=csv_file[len(proj)+14:-4] ##AI model
    ##subset data
    justdr=csv[['Evaluate', 'Expand', 'Repeat', 'Completion', 'Recall', 'Open-end', 'Wh', 'Distancing']]
    sumscore=justdr.sum() ##sum every column
    Prompt=sum(sumscore[3:8]) ##prompt score is the total of crowd
    PEER=sum(sumscore)
    # header=list(justdr.columns) ##get names of columns
    ##aggregate the data to the emptyframe
    newrow=pd.DataFrame({'ID': [kid], 'model': [model], 'PEER': [PEER],
                    'prompt': [Prompt], 'evaluate': [sumscore['Evaluate']], 'expand': [sumscore['Expand']], 'repeat': [sumscore['Repeat']],
                    'completion': [sumscore['Completion']], 'recall': [sumscore['Recall']], 'openend': [sumscore['Open-end']],
                    'wh': [sumscore['Wh']], 'distancing': [sumscore['Distancing']]})
    df=pd.concat([df, newrow])


df.to_csv('drai_summary.csv', index=False)
