# Automatic coding of parents' shared reading practice <img src="https://github.com/smy1/swlab/blob/main/script/swlogo.jpg" width=auto height="27">
- Shared reading is coded using the PEER coding scheme
  - Prompt: Ask questions using CROWD (completion, recall, open-end, wh, distancing)
  - Evaluate: Praise or correct a child's utterance
  - Expand: Elaborate on a child's utterance
  - Repeat: Request a child to say the correct answer

## Part 1: Transcribe the audio file
1. Transcribe an audio recording into an excel file (see [here](https://github.com/smy1/swlab/blob/main/script/audio2xlsx.ipynb)).
2. Convert the excel file into a csv file.

## Part 2: Code the transcript
1. Download the PEER coding scheme [here](./peer.docx).
2. Get a unique API key. Create a .env file and store the key: `GEMINI_API_KEY = the-API-key` or `OPENAI_API_KEY = the-API-key`
3. Download the Python [script](./drei.py) (which is modified from [Prof Tsai's original script](https://github.com/peculab/autogen_project/blob/main/DRai/DRai.py)).
   - To **change the AI**, go to _line 15_ and type `get_ai = "openai"` or `get_ai = "gemini"`
   - To **change the model**, go to _line 16_ and type `model = "the-model-name"`
   - To **change the prompt type**, go to _line 151_ and type one of the following:
    ```python
    content = prompt_unguided + "\n\n" + batch_text
    content = prompt_definition + "\n\n" + batch_text
    content = prompt_full + "\n\n" + batch_text
    ```
>[!TIP]
>If the prompt type is changed, it is advisable to also go to _line 202_ and change the name of the output accordingly:
>```python
>output_csv = f"{input_csv[0:-4]}_prompt=U_{model}.csv" ##for unguided prompts
>output_csv = f"{input_csv[0:-4]}_prompt=D_{model}.csv" ##for definition-provided prompts
>output_csv = f"{input_csv[0:-4]}_prompt=F_{model}.csv" ##for full-scheme prompts
>```
4. Open an editor (e.g., [Kate](https://kate-editor.org/) or [VS Code](https://code.visualstudio.com/)) and type the following:
```python
python -m venv venv #create a virtual environment the first time
.\venv\Scripts\activate #activate venv
python .\drei.py mc51.csv ##code the file "mc51"
deactivate #deactivate venv
```
## Part 3: Fancy output
1. Prof Tsai's original script stores the coded transcript as a csv file.

__Wishlist__
- Transform the scores into a 7-point Likert scale.
- Create a simple (yet appealing) html page that shows the summary of PEER scores.
- Create a plot that displays how the parent fared in relation to other parents with a similar-aged child.
- Provide some advice/encouragement as to which DR strategy the parent can improve on.
- Print this summary as a pdf to be sent to the parent (if they wish to keep a copy).
