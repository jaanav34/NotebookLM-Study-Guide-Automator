import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
# Configure your API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # type: ignore

def parse_markdown_sections(markdown_file):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    sections = {}
    # Split the content by section headers
    parts = re.split(r'## Section (\w+)', content)
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            section_id = parts[i]
            section_content = parts[i+1].strip()
            # Remove the diagram marker from the content
            section_content = re.sub(r'%%DIAGRAM_MARKER_\w+%%', '', section_content)
            sections[section_id] = section_content
    return sections

def parse_topics(topics_file):
    with open(topics_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # This is a simplified parser; you can reuse your more robust one
    topics = {}
    # A simple regex to get topic descriptions
    pattern = re.compile(r'^\(f\)\s(.*?)$', re.MULTILINE)
    for match in pattern.finditer(content):
        # This is a placeholder; you'll want to parse this properly
        # For now, we'll just get the first line
        topic_description = match.group(1)
        # A more robust parser would be needed here
        # For now, we'll just use a placeholder
        topics['1a'] = "Definition of signals..." # Replace with actual parsing
    return topics


def generate_diagram_code(section_id, section_content, topic_description):
    model = genai.GenerativeModel('gemini-2.5-flash') # type: ignore
    prompt = f"""
    You are an expert in creating EFFICIENT LaTeX diagrams for technical topics using TikZ and PGFPlots.
    Based on the content for section {section_id}, create a visually clear LaTeX diagram.

    Topic Description:
    {topic_description}

    Section Content:
    {section_content}

    **CRITICAL PERFORMANCE INSTRUCTIONS:**

    1.  **Avoid Complex Fills:** Do NOT use the `\\fill` command with complex, manually defined paths (especially paths involving curves and cycles). This is extremely slow.
    2.  **No Opacity:** Do NOT use the `opacity` or `fill opacity` options. They cause major performance issues.
    3.  **Prefer Optimized Libraries:** If shading is necessary, use the `fillbetween` library from PGFPlots, which is much faster.
    4.  **Use Annotations:** Instead of shading a "preferred region," use arrows and text labels to indicate areas, which is much faster. For example, place a node with text that says "Preferred Region" and use an arrow to point to the area.
    5.  **Keep it Simple:** The goal is a clear, fast-compiling diagram that illustrates the key concept.
    6. "When labeling arrows or lines, attach the node directly to the \\draw command using options like midway, above, or sloped. Always include clip=false in the axis options."
    Assume the necessary packages (like `tikz` and `pgfplots`) are already included in the document preamble.
        DO NOT include `\\documentclass`, `\\usepackage`, or `\\begin document ` / `\\end document` in your output.
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
    """
    # ... (rest of your function)
    try:
        response = model.generate_content(prompt)
        # (Your existing code to parse the response)
        code = response.text
        match = re.search(r'```latex\n(.*?)\n```', code, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback if the model doesn't use markdown
        code = code.replace("```latex", "").replace("```", "")
        return code.strip()
    except Exception as e:
        print(f"Error generating diagram for section {section_id}: {e}")
        return ""

def main():
    sections = parse_markdown_sections('final_study_guide.md')
    topics = parse_topics('topics.md') # You'll need to implement a parser for topics.md
    diagrams = {}

    for section_id, section_content in sections.items():
        print(f"Generating diagram for section {section_id}...")
        topic_description = topics.get(section_id, "") # Get the corresponding topic description
        if topic_description:
            diagram_code = generate_diagram_code(section_id, section_content, topic_description)
            diagrams[section_id] = diagram_code
        else:
            print(f"No topic description found for section {section_id}")


    with open('diagrams.json', 'w', encoding='utf-8') as f:
        json.dump(diagrams, f, indent=2)

    print("✅ Diagram generation complete! Check diagrams.json.")

if __name__ == "__main__":
    main()