import google.generativeai as genai
import os
import json
import re
import dotenv
# Configure your API key
dotenv.load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # type: ignore

def get_section_content(markdown_file, section_id):
    """Extracts content for a specific section from the markdown file."""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find the content of a specific section
    pattern = re.compile(rf'## Section {section_id}(.*?)(?=## Section|\Z)', re.DOTALL)
    match = pattern.search(content)

    if match:
        section_content = match.group(1).strip()
        # Remove the marker from the content before sending it to the model
        return re.sub(r'%%DIAGRAM_MARKER_\w+%%', '', section_content)
    return None

def generate_diagram_for_section(section_id, section_content):
    model = genai.GenerativeModel('gemini-2.5-flash') # type: ignore
    prompt = f"""
    You are an expert in creating EFFICIENT LaTeX diagrams for technical topics using TikZ and PGFPlots.
    Based on the content for section {section_id}, create a visually clear LaTeX diagram.

    Topic Description:
    {section_content}

    Section Content:
    {section_content}

    **CRITICAL PERFORMANCE INSTRUCTIONS:**

    1.  **Avoid Complex Fills:** Do NOT use the `\\fill` command with complex, manually defined paths (especially paths involving curves and cycles). This is extremely slow.
    2.  **No Opacity:** Do NOT use the `opacity` or `fill opacity` options. They cause major performance issues.
    3.  **Prefer Optimized Libraries:** If shading is necessary, use the `fillbetween` library from PGFPlots, which is much faster.
    4.  **Use Annotations:** Instead of shading a "preferred region," use arrows and text labels to indicate areas, which is much faster. For example, place a node with text that says "Preferred Region" and use an arrow to point to the area.
    5.  **Keep it Simple:** The goal is a clear, fast-compiling diagram that illustrates the key concept.

    **Example of a good, fast-compiling structure:**
    ```latex
    \\begin{{tikzpicture}}
        \\begin{{axis}}[
            title={{Relevant Title}},
            xlabel={{Time (t)}},
            ylabel={{Amplitude}},
            grid=both,
            axis lines=left
        ]
        % Plot a simple function
        \\addplot[blue, thick, domain=0:10] {{sin(deg(x))}};
        
        % Use nodes and arrows for annotation instead of slow fills
        \\node[align=left] at (axis cs: 7, 0.8) {{This is the\\\\\textbf{{Important Region}}}};
        \\draw[->, thick] (axis cs: 6, 0.7) -- (axis cs: 5, 0.1);

        \\end{{axis}}
    \\end{{tikzpicture}}
    ```
    
    Now, generate the efficient diagram for the provided section content.
    Assume the necessary packages (like `tikz` and `pgfplots`) are already included in the document preamble.
        DO NOT include `\\documentclass`, `\\usepackage`, or `\\begin document ` / `\\end document` in your output.
    """
    # ... (rest of your function)
    try:
        response = model.generate_content(prompt)
        code = response.text
        # Clean the response to get only the code block
        match = re.search(r'```latex\n(.*?)\n```', code, re.DOTALL)
        if match:
            return match.group(1).strip()
        return code.strip()
    except Exception as e:
        print(f"Error generating diagram for section {section_id}: {e}")
        return ""

def main():
    target_section = '1a'
    markdown_file = 'studyguides/final_study_guide copy.md' # Make sure this is the correct path

    section_content = get_section_content(markdown_file, target_section)

    if section_content:
        print(f"Generating diagram for section {target_section}...")
        diagram_code = generate_diagram_for_section(target_section, section_content)

        diagrams = {target_section: diagram_code}

        with open('diagrams.json', 'w', encoding='utf-8') as f:
            json.dump(diagrams, f, indent=2)

        print("✅ Diagram generation complete! Check diagrams.json.")
    else:
        print(f"Could not find content for section {target_section} in {markdown_file}.")

if __name__ == "__main__":
    main()