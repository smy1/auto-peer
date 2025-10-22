# Automatic coding of parents' shared reading practice <img src="https://github.com/smy1/swlab/blob/main/script/swlogo.jpg" width=auto height="27">
A video summarising the project: https://youtu.be/HqQscR9HchA  
- [background](#background)
- [usage](#usage)
<!--- [fancy output](#fancy-output)-->

---

## Background
- Shared reading is coded using the PEER coding scheme
  - Prompt: Ask questions using CROWD (completion, recall, open-end, wh, distancing)
  - Evaluate: Praise or correct a child's utterance
  - Expand: Elaborate on a child's utterance
  - Repeat: Request a child to say the correct answer
- Flowchart of the AI's task  
  <img src="./flowchart.png" width=auto height="500">
---

## Usage
### Part 1: Transcribe the audio file
1. Transcribe an audio recording into an excel file (see [here](https://github.com/smy1/swlab/blob/main/script/audio2xlsx.ipynb)).
2. Convert the excel file into a csv file (see [here](https://github.com/smy1/swlab/blob/main/script/convert_xl_csv_utf8.py)).

### Part 2: Code the transcript
1. Download a [sample transcript](./x33.csv) and the [PEER coding scheme](./peer_full.docx).
2. Get a unique API key. Create a .env file and store the key: `GEMINI_API_KEY = the-API-key` or `OPENAI_API_KEY = the-API-key`
3. Download the [main script](./drei.py), [function script](./drei_func.py), and [prompt script](./drei_prompt.py)<!-- (all of which are modified from [Prof Tsai's original script](https://github.com/peculab/autogen_project/blob/main/DRai/DRai.py))-->.
4. Open an editor (e.g., [Kate](https://kate-editor.org/) or [VS Code](https://code.visualstudio.com/)) and type the following:
```python
python -m venv venv #create a virtual environment the first time
.\venv\Scripts\activate #activate venv
## REMEMBER TO INSTALL PACKAGES
python .\drei.py x33.csv ##code the file "x33.csv"
```
5. The script will then prompt for answers:
   - **Question 1**: Are we using (G)emini or (O)penAI? **Possible input**: `g` or `o`
   - **Question 2**: Which model are we using? **Example input**: `gemini-2.0-flash` or `gpt-4o-mini`
   - **Question 3**: Are we using a(n) (U)nguided, (D)efined, or (F)ull prompt? **Possible input**: `u` or `d` or `f` (Any other response will be treated as calling for an unguided prompt.)
>[!Tip]
>- For **Question 2**, any model supported by the LLM's API should work. Check for other [OpenAI models](https://platform.openai.com/docs/models) or [Gemini models](https://ai.google.dev/gemini-api/docs/models).  
>- For **Question 3**, *unguided* means that the PEER criteria are not defined or explained in the prompt; *defined* means that simple definitions (and examples) are provided for each of the PEER criteria in the prompt; while *full* means that the entire PEER coding scheme document (originally written to guide human coders) is attached in the prompt.

---

<!--## Fancy output
1. Prof Tsai's original script stores the coded transcript as a csv file.
2. Sum of scores can be calculated using this [Python script](./summary.py).

__Wishlist__
- Compare English/Chinese prompts with English/Chinese transcripts.
- Transform the scores into a 7-point Likert scale.
- Create a simple (yet appealing) html page that displays the scores.
- Create a plot that displays how the parent fared in relation to other parents with a similar-aged child.
- Provide some advice/encouragement as to which DR strategy the parent can improve on.
- Print this summary as a pdf to be sent to the parent (if they wish to keep a copy).-->
