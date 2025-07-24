import re
import asyncio
from notebook_automator import query_notebook

# The master prompt template
PROMPT_TEMPLATE = """
Generate a structured, exam-focused textbook/study guide hybrid for ECE 270 Exam 2. Use only the provided lecture slides and past exams as sources, prioritizing lecture slides (lec_ files) over supplements (Supplement_ files). Ensure the study guide follows a structured, educational, and exam-oriented format, emphasizing conceptual clarity, problem-solving techniques, and digital circuit design strategies. Also include exam style problems and explanations. The past exams and their solutions have been provided. To make each section as long as possible, output section by section and wait. Continue with section {X}. Do not waste tokens on introducing or summarizing a section.

Formatting Instructions:
Include (only when related to current section) truth tables, circuit diagrams, k-maps and Boolean expressions formatted in LaTeX
Use bullet points for key concepts and step-by-step derivations
Ensure the study guide is structured for easy last-minute review while maintaining depth
Goal:
This study guide should be a hybrid between a textbook and an exam-oriented manual, with clear explanations, step-by-step circuit derivations, and practical problem-solving techniques. Ensure it is fully aligned with the ECE 270 Exam 2 objectives and optimized for efficient exam preparation.

Important Notes:
Follow structured formatting, using section headers, definitions, examples, and problem-solving steps.

{Y}
"""


def parse_topics(filename="topics.md"):
    """
    Parses a detailed, multi-line topics.md file into structured sections across multiple major headings.
    Handles:
      - Multiple major sections (e.g., "1. Title", "2. Title", ...)
      - Subsections (a, b, c, ...), preserving full blocks
      - Prefixing the major title only for subsection 'a'
    Returns a list of dicts: [{'id': '1a', 'title': '1. Title\n\n(a) ...'}, ...]
    """
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    sections = []
    # Regex to match each major section and its content
    # Explicitly consume the newline after the header to capture body correctly
    major_pattern = re.compile(
        r"^(?P<num>\d+)\.\s*(?P<header>.+?)\s*$\n"
        r"(?P<body>.*?)(?=^\d+\.|\Z)",
        flags=re.MULTILINE | re.DOTALL
    )

    for major in major_pattern.finditer(text):
        major_num = major.group('num')
        major_header = f"{major_num}. {major.group('header').strip()}"
        body = major.group('body').strip()

        # Split into subsections, keeping the marker '(a)', '(b)', etc.
        parts = re.split(r'(?=^\([a-z]\))', body, flags=re.MULTILINE)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            sub_m = re.match(r"^\(([a-z])\)", part)
            if not sub_m:
                continue
            letter = sub_m.group(1)
            sec_id = f"{major_num}{letter}"

            # Prefix only the 'a' block with the major header
            title = f"{major_header}\n\n{part}" if letter == 'a' else part
            sections.append({'id': sec_id, 'title': title})

    return sections




async def generate_study_guide():
    """Main function to run the conversation and build the guide."""
    print("Parsing topics from topics.md...")
    topics = parse_topics()
    full_study_guide = []

    print(f"Found {len(topics)} sections to generate.")
    
    # This will create a new, empty file at the start of the conversation
    with open("final_study_guide.md", "w") as f:
        f.write("# ECE 270 Exam 2 Study Guide\n\n")

    for i, topic in enumerate(topics):
        section_id = topic['id']
        section_title = topic['title']
        
        print(f"--- Generating Section {section_id}: {section_title} ({i+1}/{len(topics)}) ---")

        # Format the prompt for the current section
        prompt = PROMPT_TEMPLATE.format(X=section_id, Y=section_title)
        
        # Call the scraper
        response_md = await query_notebook(prompt)
        
        if "error" in response_md.lower():
            print(f"An error occurred: {response_md}")
            break # Stop if there's an error

        # Append the response to the final file
        with open("final_study_guide.md", "a", encoding="utf-8") as f:
            # The 'title' now contains the full description, which we don't need to repeat.
            # We will just write a simple header.
            f.write(f"## Section {section_id}\n\n")
            f.write(response_md)
            f.write("\n\n---\n\n")
            
        print(f"✓ Section {section_id} complete and saved.")

    print("\n\n✅ Study guide generation complete!")
    print("Your file is ready: final_study_guide.md")


if __name__ == "__main__":
    asyncio.run(generate_study_guide())