import os
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
INPUT_FILENAME = "final_study_guide.md"
OUTPUT_FILENAME = "study_guide.tex"
MODEL_NAME = "gemini-2.0-flash" # Or any other suitable model like "gemini-1.0-pro"

# This LaTeX header is taken directly from your prompt
LATEX_HEADER = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{array}
\usepackage{booktabs}
\usepackage{listings}
\usepackage{color}
\usepackage{graphicx}

\usepackage[paperwidth=8.5in,paperheight=11.0in,
  left=0.35in,right=0.35in,top=0.3in,bottom=0.15in,
  includefoot,heightrounded]{geometry}

\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{} % Clear existing headers/footers
\fancyhead[R]{\textbf{Shah958, Jaanav Shah}} % Right-aligned header
\renewcommand{\headrulewidth}{0pt} % Remove header rule (optional)
\fancyfoot[R]{\textbf{Shah958, Jaanav Shah} \quad | \quad \textbf{Page \thepage}} % Right-aligned footer with page number
\renewcommand{\footrulewidth}{0pt} % Remove footer rule (optional)
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}

\lstset{style=mystyle}

\begin{document}
"""

class LatexConverter:
    """
    A class to handle the conversion of Markdown to LaTeX using the Gemini API.
    The retry logic is adapted from your 'pipeline.py' file.
    """
    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=self.api_key) # type: ignore
        self.model = genai.GenerativeModel(self.model_name) # type: ignore
        print(f"Gemini model '{self.model_name}' initialized.")

    def _make_llm_call_with_retries(self, prompt: str, max_retries: int = 3):
        """
        Makes an API call with a retry mechanism, now with streaming enabled
        to handle large outputs beyond the 8k token limit.
        """
        for attempt in range(max_retries):
            try:
                print(f"Making API call with streaming (Attempt {attempt + 1}/{max_retries})...")
                # Add stream=True to the generation call
                response_stream = self.model.generate_content(prompt, stream=True)
                
                # Iterate through the chunks and build the full response
                full_response = []
                for chunk in response_stream:
                    full_response.append(chunk.text)
                
                return "".join(full_response)

            except Exception as e:
                print(f"API call failed with error: {e}")
                if attempt < max_retries - 1:
                    sleep_time = 2 ** (attempt + 1)
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("Max retries reached. Aborting.")
                    raise

    def convert(self, markdown_text: str):
        """
        Constructs the full prompt and calls the LLM to perform the conversion.
        """
        prompt = f"""
Your task is to convert the following Markdown text into a LaTeX document.

**Instructions:**
1.  Convert the Markdown to LaTeX as faithfully as possible.
2.  DO NOT change any of the actual content, wording, or text.
3.  DO NOT omit any content. The entire document must be converted.
4.  You MUST exclude conversational filler text like "here is the section," "of course," or "please let me know when you're ready for the next section." Only convert the actual study guide content.
5.  Use the provided LaTeX header.
6.  Do not leave any unicode characters in the latex; replace them with latex friendly methods eg. bullet points like LaTeX Error: Unicode character ▪ (U+25AA) should be instead the itemize method, or Unicode character ⁿ (U+207F) which is a superscript n should be replaced with \textsuperscript{{n}}.
7.  Make the overall document look aesthetic as heckkkkk: use all the provided headers to make the LaTeX beautiful.

@@@ LATEX HEADER TO USE @@@
{LATEX_HEADER}

@@@ MARKDOWN CONTENT TO CONVERT @@@
{markdown_text}

@@@ END OF MARKDOWN CONTENT @@@
\\end{{document}}
"""
        return self._make_llm_call_with_retries(prompt)


def clean_markdown_for_conversion(markdown_text: str) -> str:
    """Removes conversational filler from the study guide before sending to the LLM."""
    # This regex looks for common conversational phrases and removes the entire line
    patterns = [
        re.compile(r".*(here is the section|here's the next part|let me know when you're ready|continuing with section).*\n?", re.IGNORECASE),
        re.compile(r".*(of course|certainly|alright).*\n?", re.IGNORECASE)
    ]
    
    cleaned_text = markdown_text
    for pattern in patterns:
        cleaned_text = pattern.sub("", cleaned_text)
        
    return cleaned_text.strip()


def main():
    """Main function to run the conversion process."""
    print("--- Starting Markdown to LaTeX Converter ---")
    
    # 1. Get API Key
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        return

    # 2. Read the input Markdown file
    try:
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        print(f"Successfully read '{INPUT_FILENAME}'.")
    except FileNotFoundError:
        print(f"ERROR: Input file '{INPUT_FILENAME}' not found.")
        return

    # 3. Clean the Markdown of conversational filler
    cleaned_md = clean_markdown_for_conversion(markdown_content)
    print("Cleaned conversational filler from the markdown.")

    # 4. Initialize the converter and run the conversion
    try:
        converter = LatexConverter(api_key=api_key)
        latex_output = converter.convert(cleaned_md)

        # 5. Save the output
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write(latex_output)
        print(f"\n✅ Success! LaTeX output saved to '{OUTPUT_FILENAME}'.")
        
    except Exception as e:
        print(f"\n❌ An error occurred during the conversion process: {e}")


if __name__ == "__main__":
    main()