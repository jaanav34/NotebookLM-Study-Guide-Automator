import os
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv
import unicodedata
import json

load_dotenv()

# --- Configuration ---
INPUT_FILENAME = "studyguides/final_study_guide copy.md"
OUTPUT = "studyguides/study_guide.tex"
CLEAN = "studyguides/study_guide_CLEAN.tex"
MODEL_NAME = "gemini-2.5-pro" # Or any other suitable model like "gemini-1.0-pro"
# ─── Global toggle: strip all circuitikz environments? ───────────────────────
REMOVE_TIKZ_BLOCKS = True
CHEATSHEET = False
# This LaTeX header is taken directly from your prompt
if(CHEATSHEET!=True):
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
\usepackage{pgfplots} % <<< ADD THIS
\pgfplotsset{compat=1.18} % <<< AND THIS for compatibility
\usetikzlibrary{external} % <<< ADD THIS
\tikzexternalize% <<< AND THIS
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
else:
    LATEX_HEADER = r"""
\documentclass[10pt]{article}
\usepackage[framemethod=TikZ]{mdframed}
\usepackage{amsthm}
\usepackage[landscape]{geometry}
\usepackage{multicol}
\usepackage{tikz}
\usepackage{xcolor}
\usepackage{amsmath}
\usepackage[T1]{fontenc}
\usepackage{utopia}
\usepackage{changepage}
\usepackage{amssymb}
\usepackage{fancyhdr}
\usepackage[many]{tcolorbox}
\usepackage{fullpage}
\usepackage{listings}
\usepackage{booktabs}
\usepackage{mathpazo}
\usetikzlibrary{circuits.logic.US,circuits.logic.IEC}
\lstset{language=Verilog,
  basicstyle=\ttfamily\footnotesize,
  keywordstyle=\color{blue}\bfseries,
  commentstyle=\color{gray}\itshape,
  stringstyle=\color{red},
  frame=single,
  breaklines=true,
  postbreak=\mbox{\textcolor{red}{$\hookrightarrow$}\space},
}

\usepackage{tcolorbox}
\newtcolorbox{conceptbox}[2][]{
  breakable,
  enhanced,
  before skip=4pt,
  after skip=4pt,
  left=2pt, right=2pt, top=2pt, bottom=2pt,
  boxrule=0.8pt,
  colframe=#1!70!black,
  colback=#1!20,
  title=\scriptsize\bfseries #2
}


%

% Color definitions ... (same as draft)
\definecolor{r1}{RGB}{255, 191, 191}
\definecolor{r2}{RGB}{255, 191, 223}
\definecolor{r3}{RGB}{255, 207, 207}
\definecolor{b1}{RGB}{191, 223, 255}
\definecolor{b2}{RGB}{191, 239, 255}
\definecolor{b3}{RGB}{191, 255, 255}
\definecolor{g1}{RGB}{191, 255, 191}
\definecolor{g2}{RGB}{191, 255, 223}
\definecolor{g3}{RGB}{207, 255, 207}
\definecolor{o1}{RGB}{255, 223, 191}
\definecolor{o2}{RGB}{255, 239, 191}
\definecolor{o3}{RGB}{255, 231, 191}
\definecolor{v1}{RGB}{223, 191, 255}
\definecolor{v2}{RGB}{239, 191, 255}
\definecolor{v3}{RGB}{231, 191, 255}
\definecolor{y1}{RGB}{255, 255, 191}
\definecolor{y2}{RGB}{255, 247, 191}
\definecolor{y3}{RGB}{255, 239, 191}
\definecolor{w}{HTML}{eeeeee}
\definecolor{g}{HTML}{444444}
\definecolor{b}{HTML}{222222}
\definecolor{lightgrey}{HTML}{cccccc}
\geometry{ letterpaper, left=0.25in, right=0.25in, top=0.15in, bottom=0.25in}
\pagestyle{fancy}
\fancyhf{}
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
        'â€™': "'",            # Incorrect apostrophe
        'â€¦': '...',        # Incorrect ellipsis
        'â—¦': r'    \item',  # NEW: Converts unicode bullet to an indented item
        # Add more rules here as needed, for example:
        # '²': '^{2}',
        # '³': '^{3}',
    }
    
    latex_content = latex_content
    for find_char, replace_with in cleaning_rules.items():
        latex_content = latex_content.replace(find_char, replace_with)    
    
    # latex_content = escape_plaintext_underscores_and_superscripts(latex_content)
    # **New step**: fix those stray single-backslashes in tables
    latex_content = fix_tabular_row_separators(latex_content)
    latex_content = break_table_rows(latex_content)
    latex_content = fix_hlines_by_line(latex_content)
    latex_content = re.sub(r'\[\s*(\\begin{tikzpicture}.*?)\\end{tikzpicture}\s*\]',
               r'\1\\end{tikzpicture}', latex_content, flags=re.DOTALL)
    latex_content = fix_carets(latex_content)
    # This call will wrap all blocks of lonely items in an itemize environment.
    latex_content = fix_lonely_items(latex_content)

    # You can also add more complex regex substitutions here if needed
    # For example, to remove lines that only contain '\hrulefill'
    latex_content = re.sub(r'^\s*\\hrulefill\s*$', '', latex_content, flags=re.MULTILINE)
    if REMOVE_TIKZ_BLOCKS:
        latex_content = remove_tikz_blocks(latex_content)
    # latex_content = remap_fourth_itemize(latex_content)
    latex_content = re.sub(r'[\u0080-\uFFFF]', replace_unicode_char, latex_content)

    def fix_enumerate(match):
        # Takes a matched block of text
        block = match.group(0)
        # Replaces each numbered line start with \item
        items = re.sub(r'\d+\\\.\s*', r'\\item ', block)
        # Wraps the entire block in the enumerate environment
        return f"\\begin{{enumerate}}\n{items}\n\\end{{enumerate}}"

    # This regex finds consecutive lines starting with "1\. ", "2\. ", etc.
    # and passes the whole block to the fix_enumerate function
    latex_content = re.sub(r'((\d+\\\. .*(\n|$))+)', fix_enumerate, latex_content)

    # Add the diagram replacement step at the end
    latex_content = replace_diagram_markers(latex_content)

    print("Cleaning complete.")
    return latex_content
def replace_diagram_markers(latex_content):
    try:
        with open('diagrams.json', 'r', encoding='utf-8') as f:
            diagrams = json.load(f)
    except FileNotFoundError:
        print("diagrams.json not found. No diagrams will be inserted.")
        return latex_content

    for section_id, diagram_code in diagrams.items():
        marker = f"%%DIAGRAM_MARKER_{section_id}%%"
        if diagram_code:
            # You might want to wrap the diagram in a figure environment
            replacement = (
                "\\begin{figure}[h!]\n"
                "\\centering\n"
                f"{diagram_code}\n"
                f"\\caption{{Diagram for section {section_id}}}\n"
                "\\end{figure}"
            )
            latex_content = latex_content.replace(marker, replacement)
        else:
            # If no diagram was generated, just remove the marker
            latex_content = latex_content.replace(marker, "")
    return latex_content

def remap_fourth_itemize(text: str) -> str:
    """
    Walks through the LaTeX text, tracks itemize depth,
    and whenever it would start the 4th level, swaps in itemizeDeep
    (and likewise for the matching \\end).
    """
    out = []
    depth = 0
    for line in text.splitlines(keepends=True):
        if r'\begin{itemize}' in line:
            depth += 1
            if depth == 4:
                out.append(line.replace('itemize', 'itemizeDeep'))
            else:
                out.append(line)
        elif r'\end{itemize}' in line:
            if depth == 4:
                out.append(line.replace('itemize', 'itemizeDeep'))
            else:
                out.append(line)
            depth -= 1
        else:
            out.append(line)
    return ''.join(out)

def fix_lonely_items(latex_content: str) -> str:
    """
    Finds blocks of consecutive 'lonely' \\item lines and wraps them
    in a \\begin{itemize}...\\end{itemize} environment.
    This version correctly handles both lonely items and existing list environments.
    """
    # This pattern has two parts separated by an OR operator `|`:
    # 1. `(\\begin\{(?:itemize|enumerate)\}.*?\\end\{(?:itemize|enumerate)\})`:
    #    This captures any existing, correctly-formed itemize or enumerate block.
    #    The `re.DOTALL` flag is essential for `.` to match across newlines.
    # 2. `((?:^\s*\\item.*\n?)+)`:
    #    This captures a block of one or more consecutive "lonely" item lines.
    #    The `re.MULTILINE` flag is needed for `^` to match the start of each line.
    pattern = re.compile(
        r'(\\begin\{(?:itemize|enumerate)\}.*?\\end\{(?:itemize|enumerate)\})|((?:^\s*\\item.*\n?)+)',
        re.DOTALL | re.MULTILINE
    )

    def wrap_if_lonely(match):
        # The match object will have one of two groups populated.
        # Group 1: The correctly-formed list block.
        # Group 2: The lonely item block.
        
        # If group 1 matched, it's an existing list. Return it unchanged.
        if match.group(1):
            return match.group(1)
        
        # If group 2 matched, it's a lonely block. Wrap it.
        elif match.group(2):
            block = match.group(2)
            return f"\\begin{{itemize}}\n{block.strip()}\n\\end{{itemize}}\n"
        
        # Should not happen, but return original text just in case
        return match.group(0)

    return pattern.sub(wrap_if_lonely, latex_content)



def escape_plaintext_underscores_and_superscripts(text: str) -> str:
    """
    In all non‑math segments (i.e. outside $…$ or \\[…\\]):
      1) Escape lone underscores (_) → \\_
      2) Turn digit^letter → digit$^letter$
    """
    # Split on math segments \[...\] (display math) or $...$ (inline math)
    parts = re.split(r'(\$.*?\$|\\\[.*?\\\])', text, flags=re.DOTALL)
    for idx in range(0, len(parts), 2):   # only plaintext bits
        pt = parts[idx]
        # 1) escape any _ that's not already \_
        pt = re.sub(r'(?<!\\)_', r'\\_', pt)
        # 2) convert, e.g., "2^n" → "2$^n$"
        #    only when a digit(s) is directly followed by ^letter/number
        pt = re.sub(r'(\d+)\^([A-Za-z0-9])', r'\1$^\2$', pt)
        parts[idx] = pt
    return ''.join(parts)

def replace_unicode_char(match):
    ch = match.group(0)
    cp = ord(ch)

    # 1) Very common typographic apostrophe
    if cp == 0x2019:   # RIGHT SINGLE QUOTATION MARK
        return "'"

    # 2) Arrows →, ←, etc.
    if cp == 0x2192:   # →
        return r'$\rightarrow$'
    if cp == 0x2190:   # ←
        return r'$\leftarrow$'
    if cp == 0x21D2:   # ⇒
        return r'$\Rightarrow$'
    if cp == 0x21D0:   # ⇐
        return r'$\Leftarrow$'

    name = unicodedata.name(ch, '').upper()

    # 3) Superscripts/subscripts
    if 'SUPERSCRIPT' in name:
        part = name.rsplit()[-1].lower()
        return f'$^{{{part}}}$'
    if 'SUBSCRIPT' in name:
        part = name.rsplit()[-1].lower()
        return f'$_{{{part}}}$'

    # 4) A few other named symbols
    known = {
        'BULLET':     r'\item',    # •
        'ELLIPSIS':   '...',       # …
        'MINUS':      '-',         # −
        'MULTIPLICATION SIGN': r'$\times$',
        'DIVISION SIGN':       r'$\div$',
        # add more as you discover them
    }
    for key, rep in known.items():
        if key in name:
            return rep

    # 5) If it's in 0x00–0xFF, let LaTeX char handle it:
    if cp <= 0xFF:
        return f'\\char"{cp:02X}'

    # 6) Otherwise drop it (or replace with a placeholder)
    return ''  # or return '?'  

def fix_tabular_row_separators(text: str) -> str:
    """
    Finds every \\begin{tabular}…\\end{tabular} block and inside it
    replaces occurrences of
        space + backslash + space
    (i.e. ' \\ ')
    with
        space + double-backslash + space
    (i.e. ' \\\\ '),
    preserving everything else exactly.
    """
    TAB_PATTERN = re.compile(
        r'(\\begin\{tabular\}.*?\\end\{tabular\})',
        flags=re.DOTALL
    )

    def transform(match):
        block = match.group(1)
        # only replace lone " \ " sequences—not \hline or any other \
        return block.replace(' \\ ', ' \\\\ ')

    return TAB_PATTERN.sub(transform, text)


def remove_tikz_blocks(text: str) -> str:
    """
    Removes everything from
      \\begin{circuitikz} … \\end{circuitikz}
    and
      \\begin{tikzpicture} … \\end{tikzpicture}
    inclusive. Single‐pass DOTALL regex.
    """
    pattern = re.compile(
        r'\\begin\{(?:circuitikz|tikzpicture)\}'
        r'.*?'
        r'\\end\{(?:circuitikz|tikzpicture)\}',
        flags=re.DOTALL
    )
    return pattern.sub('', text) 


def fix_carets(text: str) -> str:
    # 1) Split into segments: non‐math, math, non‐math, math, …
    parts = re.split(r'(\$.*?\$)', text)

    # 2) Only in the math parts (odd indices) replace \^ with \char94
    for i in range(1, len(parts), 2):
        # Replace literal \^ with \char94
        parts[i] = re.sub(r'\\\^', r'\\char94', parts[i])

    # 3) Rejoin everything
    return ''.join(parts)


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

            with open(OUTPUT, 'w', encoding='utf-8') as f:
                f.write(final_latex)
            print(f"\n✅ Success! Full LaTeX document assembled and saved to '{OUTPUT}'.")

            # Apply the new post-processing function
            final_latex = post_process_latex(final_latex)

            with open(CLEAN, 'w', encoding='utf-8') as f:
                f.write(final_latex)
            print(f"\n✅ Success! Clean LaTeX document assembled and saved to '{CLEAN}'.")
            
        except Exception as e:
            print(f"\n❌ An error occurred during the AI conversion process: {e}")

    elif mode == 'n':
        # --- CLEANER-MODE ---
        print(f"\nRunning in Cleaner-only mode on '{OUTPUT}'...")
        try:
            with open(OUTPUT, 'r', encoding='utf-8') as f:
                existing_latex = f.read()
            
            # Apply the post-processing function to the existing file
            cleaned_latex = post_process_latex(existing_latex)
            
            with open(CLEAN, 'w', encoding='utf-8') as f:
                f.write(cleaned_latex)
            
            print(f"✅ Success! Cleaned LaTeX has been saved back to '{CLEAN}'.")
            
        except FileNotFoundError:
            print(f"ERROR: The file '{OUTPUT}' does not exist. Run AI-mode first to create it.")
        except Exception as e:
            print(f"\n❌ An error occurred during the cleaning process: {e}")
            
    else:
        print("Invalid choice. Please run the script again and enter 'Y' or 'N'.")

if __name__ == "__main__":
    main()