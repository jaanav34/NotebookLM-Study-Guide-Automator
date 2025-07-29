import os
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
INPUT_FILENAME = "final_study_guide.md"
OUTPUT_FILENAME = "study_guide"
MODEL_NAME = "gemma-3-27b-it" # Or any other suitable model like "gemini-1.0-pro"

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
\usepackage{tikz}

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
LATEX_FOOTER = r"""
\end{document}
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
        """Makes an API call with a retry mechanism."""
        for attempt in range(max_retries):
            try:
                # Streaming is not necessary for smaller chunks, simplifying the logic.
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"API call failed with error: {e}")
                if attempt < max_retries - 1:
                    sleep_time = 2 ** (attempt + 1)
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print("Max retries reached. Aborting.")
                    raise


    def convert_chunk(self, markdown_chunk: str, chunk_num: int, total_chunks: int):
        """
        Constructs the full prompt and calls the LLM to perform the conversion.
        """
        prompt = f"""
Your task is to convert the following chunk of a Markdown document into LaTeX.

This is chunk {chunk_num} of {total_chunks}.

**Instructions:**
1.  Convert the Markdown to LaTeX as faithfully as possible.
2.  DO NOT change any of the actual content, wording, or text.
3.  DO NOT omit any content. The entire chunk must be converted.
4.  You MUST exclude conversational filler text like "here is the section," "of course," or "please let me know when you're ready for the next section." Only convert the actual study guide content.
5.  Use the provided LaTeX header's options to fulfill the latex code.
6.  Do not leave any unicode characters in the latex; replace them with latex friendly methods eg. bullet points like LaTeX Error: Unicode character ▪ (U+25AA) should be instead the itemize method, or Unicode character ⁿ (U+207F) which is a superscript n should be replaced with \textsuperscript{{n}}.
7.  DO NOT add any introductory or concluding phrases. Only output the raw LaTeX for this chunk.
8.  Ensure that LaTeX environments (like itemize, tables, etc.) are properly opened and closed within this chunk.
9.  Make the overall document look aesthetic as heckkkkk: use all the provided headers to make the LaTeX beautiful.

**CRITICAL INSTRUCTIONS:**
1.  You MUST NOT include the LaTeX preamble, `\\documentclass`, `\\usepackage`, `\\begin{{document}}`, or `\\end{{document}}`.
2.  You are converting ONLY a small part of the document (chunk {chunk_num} of {total_chunks}).
3.  Your output must be ONLY the raw LaTeX code for the provided chunk, starting directly with the content (e.g., `\\section{{...}}` - get rid of the markdown like ## section 1 or similar).
4.  Do not add any comments or explanations. Your entire response will be stitched directly into the final `.tex` file.

**SPECIFIC CONVERSION RULES:**
* **Circuit Diagrams (`circuitikz`):** If you see a `\\begin{{circuitikz}}...\\end{{circuitikz}}` block, you MUST preserve it exactly as it is, without any changes.
* **Tables:** Convert Markdown tables into proper LaTeX `tabular` environments. Ensure they are correctly formatted.
* **Verilog/Code Blocks:** Wrap any SystemVerilog or other code blocks inside a `\\begin{{lstlisting}}...\\end{{lstlisting}}` environment.
* **Math Expressions:** Preserve any inline LaTeX math expressions (e.g., `$W \\cdot X'$`) exactly as they are. If you detect any math that is in a line that hasn't been inlined, inline it using $ $
* **Headings:** Convert Markdown headings (`## Section...`) into LaTeX sectioning commands (`\\section*{{...}}`, `\\subsection*{{...}}`). BELOW IS AN EXAMPLE THAT NEEDS TO BE ADHERED TO FOR ALL SECTIONS NOT JUST SECTION 1!
* ** EXAMPLE: @@@## Section 1a \\n Here is the structured study guide content for section 1a: \\n \\n 1\\. SoP, PoS, K-Maps, and Timing Hazards (30%) \\n (a) Sum of Products (SoP) and Product of Sums (PoS) Representations@@@ should be converted to this --> \\section{{SoP, PoS, K-Maps, and Timing Hazards (30%)}} \\n \\subsection{{Sum of Products (SoP) and Product of Sums (PoS)}} (do the same for all sections) so it can be referred to in a table of contents.
* **Bold/Italics:** Convert `**text**` to `\\textbf{{text}}` and `*text*` or `_text_` to `\\textit{{text}}`.


@@@ LATEX HEADER TO USE @@@
{LATEX_HEADER}

@@@ MARKDOWN CHUNK TO CONVERT @@@
{markdown_chunk}

@@@ END OF MARKDOWN CHUNK @@@
"""
        return self._make_llm_call_with_retries(prompt)


def clean_and_chunk_markdown(markdown_text: str) -> list:
    """Removes filler and splits the markdown into logical chunks by section."""
    # First, remove conversational filler from the entire text

    # This regex looks for common conversational phrases and removes the entire line
    patterns = [
        re.compile(r".*(here is the first section|here is the section|here's the next part|let me know when you're ready|continuing with section).*\n?", re.IGNORECASE),
        re.compile(r".*(of course|certainly|alright).*\n?", re.IGNORECASE)
    ]
    
    cleaned_text = markdown_text
    for pattern in patterns:
        cleaned_text = pattern.sub("", cleaned_text)
        
    # Split the document into chunks based on "## Section" headers
    # The regex includes the header in the chunk itself.

    chunks = re.split(r'(?=## Section \w+)', cleaned_text.strip())

    # Filter out any empty strings that may result from the split
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def post_process_latex(latex_content: str) -> str:
    """
    Applies a series of final cleaning rules to the generated LaTeX document.
    This is a modular function you can easily add new rules to.
    """
    print("Applying post-processing cleaning rules...")

    # --- EDIT THIS DICTIONARY TO ADD MORE RULES ---
    # Add any unicode characters or patterns here that you want to replace.
    # Key: The text/character to find.
    # Value: The LaTeX text to replace it with.
    cleaning_rules = {
        'ⁿ': '$^{n}$',         # Superscript 'n' for exponents
        '^n': '$^{n}$',
        'â€™': "'",            # Incorrect apostrophe
        'â€¦': '...',        # Incorrect ellipsis
        'â—¦': r'    \item',  # NEW: Converts unicode bullet to an indented item
        # Add more rules here as needed, for example:
        # '²': '^{2}',
        # '³': '^{3}',
    }
    
    processed_content = latex_content
    for find_char, replace_with in cleaning_rules.items():
        processed_content = processed_content.replace(find_char, replace_with)    
    
    processed_content = break_table_rows(processed_content)
    processed_content = fix_hlines_by_line(latex_content)
    processed_content = re.sub(r'\[\s*(\\begin{tikzpicture}.*?)\\end{tikzpicture}\s*\]',
               r'\1\\end{tikzpicture}', processed_content, flags=re.DOTALL)



    # You can also add more complex regex substitutions here if needed
    # For example, to remove lines that only contain '\hrulefill'
    processed_content = re.sub(r'^\s*\\hrulefill\s*$', '', processed_content, flags=re.MULTILINE)
    
    def fix_enumerate(match):
        # Takes a matched block of text
        block = match.group(0)
        # Replaces each numbered line start with \item
        items = re.sub(r'\d+\\\.\s*', r'\\item ', block)
        # Wraps the entire block in the enumerate environment
        return f"\\begin{{enumerate}}\n{items}\n\\end{{enumerate}}"

    # This regex finds consecutive lines starting with "1\. ", "2\. ", etc.
    # and passes the whole block to the fix_enumerate function
    processed_content = re.sub(r'((\d+\\\. .*(\n|$))+)', fix_enumerate, processed_content)



    print("Cleaning complete.")
    return processed_content

def fix_hlines_by_line(text: str) -> str:
    lines = text.split('\n')
    out = []
    for line in lines:
        if '\\hline' in line:
            # check whether the literal before \hline is "\\" (row‑break) already
            prefix, rest = line.split('\\hline', 1)
            if not prefix.endswith('\\\\ '):  
                # inject exactly one row‑break + space
                line = prefix + '\\\\ ' + '\\hline' + rest
        out.append(line)
    return '\n'.join(out)

def break_table_rows(text: str) -> str:
    # First, collapse any "\ \\\" into "\\" (stray extra backslashes)
    text = re.sub(r'\\\s*\\\\', r'\\\\', text)

    # 1) after any \cline{…}
    text = re.sub(r'(\\cline\{[0-9,-]*\})', r'\1\n', text)
    # 2) after a correct row-break+hline: \\ \hline
    text = re.sub(r'(\\\\\s*\\hline)', r'\1\n', text)
    # 3) if an \hline is followed by content (no newline), break before that content
    text = re.sub(r'(\\hline)\s*([A-Za-z\\\\])', r'\1\n\2', text)
    # 4) ensure \end{tabular} is on its own line
    text = re.sub(r'(\\end\{tabular\})', r'\n\1\n', text)
    return text


def main():
    """Main function to run the conversion process in one of two modes."""
    print("--- Markdown to LaTeX Converter ---")
    
    mode = input("Choose mode: [Y] AI Conversion or [N] Clean Existing .tex File? (Y/N): ").strip().lower()

    if mode == 'y':
        # --- AI-MODE ---
        print("\nRunning in AI Conversion mode...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable is not set.")
            return

        try:
            with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            print(f"Successfully read '{INPUT_FILENAME}'.")
        except FileNotFoundError:
            print(f"ERROR: Input file '{INPUT_FILENAME}' not found.")
            return

        chunks = clean_and_chunk_markdown(markdown_content)
        total_chunks = len(chunks)
        if total_chunks == 0:
            print("No content found in the markdown file after cleaning.")
            return
        print(f"Split document into {total_chunks} chunks.")

        try:
            converter = LatexConverter(api_key=api_key)
            full_latex_output = []

            for i, chunk in enumerate(chunks):
                chunk_num = i + 1
                print(f"\n--- Converting Chunk {chunk_num}/{total_chunks} ---")
                latex_part = converter.convert_chunk(chunk, chunk_num, total_chunks)
                full_latex_output.append(latex_part)
                print(f"✓ Chunk {chunk_num} converted successfully.")

            # Assemble the document
            final_latex = LATEX_HEADER + "\n\n" + "\n\n".join(full_latex_output) + "\n\n" + LATEX_FOOTER

            with open(OUTPUT_FILENAME+'.tex', 'w', encoding='utf-8') as f:
                f.write(final_latex)
            print(f"\n✅ Success! Full LaTeX document assembled and saved to '{OUTPUT_FILENAME+'.tex'}'.")

            # Apply the new post-processing function
            final_latex = post_process_latex(final_latex)

            with open(OUTPUT_FILENAME+'_CLEAN'+'.tex', 'w', encoding='utf-8') as f:
                f.write(final_latex)
            print(f"\n✅ Success! Clean LaTeX document assembled and saved to '{OUTPUT_FILENAME+'_CLEAN'+'.tex'}'.")
            
        except Exception as e:
            print(f"\n❌ An error occurred during the AI conversion process: {e}")

    elif mode == 'n':
        # --- CLEANER-MODE ---
        print(f"\nRunning in Cleaner-only mode on '{OUTPUT_FILENAME+'.tex'}'...")
        try:
            with open(OUTPUT_FILENAME+'.tex', 'r', encoding='utf-8') as f:
                existing_latex = f.read()
            
            # Apply the post-processing function to the existing file
            cleaned_latex = post_process_latex(existing_latex)
            
            with open(OUTPUT_FILENAME+'_CLEAN'+'.tex', 'w', encoding='utf-8') as f:
                f.write(cleaned_latex)
            
            print(f"✅ Success! Cleaned LaTeX has been saved back to '{OUTPUT_FILENAME+'CLEAN'+'.tex'}'.")
            
        except FileNotFoundError:
            print(f"ERROR: The file '{OUTPUT_FILENAME}' does not exist. Run AI-mode first to create it.")
        except Exception as e:
            print(f"\n❌ An error occurred during the cleaning process: {e}")
            
    else:
        print("Invalid choice. Please run the script again and enter 'Y' or 'N'.")

if __name__ == "__main__":
    main()