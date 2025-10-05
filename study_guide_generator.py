import re
import asyncio
from notebook_automator import query_notebook

# The master prompt template
PROMPT_TEMPLATE = """
Generate a structured, exam-focused textbook/study guide hybrid for ECE 301: Signals and Systems Midterm 1. Use only the provided lecture slides (M1–M6), homework + solutions (1–5), syllabus, the past exam (ECE301_Fall_2022_Exam_1.pdf), and Alan V. Oppenheim, Signals and Systems. Prioritize current semester lecture slides and homework over older sources.
The study guide must combine textbook-level clarity with exam precision, optimized for last-minute review.

For each topic:
Provide clear definitions, properties, and equations in LaTeX.
Show conceptual links (e.g., energy vs. power, continuous vs. discrete).
Include step-by-step derivations or proofs when relevant.
Do not include any example problems or numerical solutions unless explicitly stated in that subsection.
At the end of each subsection, list what content must not be included (e.g., exclude Fourier or convolution material).
Strictly obey these do-not-include boundaries to prevent overlap between sections.

Formatting:
Use bullet points and natural language explanations.
Avoid summaries or introductions of the current subsection.
Goal: Produce a technical, exam-oriented hybrid between an ECE signals textbook and an applied manual, precisely aligned with Midterm 1 coverage.

Continue with section {X}.
Current section: 
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
        f.write("# ECE 301 Quiz 1 Study Guide\n\n")

    for i, topic in enumerate(topics):
        section_id = topic['id']
        section_title = topic['title']

        print(f"--- Generating Section {section_id}: {section_title} ({i+1}/{len(topics)}) ---")

        # Format the prompt for the current section
        prompt = PROMPT_TEMPLATE.format(X=section_id, Y=section_title)

        # Call the scraper
        response_md = await query_notebook(prompt)

        if response_md.lower().startswith("error"):
            print(f"An error occurred: {response_md}")
            break # Stop if there's an error

        # Append the response to the final file
        with open("final_study_guide.md", "a", encoding="utf-8") as f:
            # The 'title' now contains the full description, which we don't need to repeat.
            # We will just write a simple header.
            f.write(f"## Section {section_id}\n\n")
            f.write(response_md)
            # Add the diagram marker
            f.write(f"\n\n%%DIAGRAM_MARKER_{section_id}%%\n\n")
            f.write("\n\n---\n\n")

        print(f"✓ Section {section_id} complete and saved.")

    print("\n\n✅ Study guide generation complete!")
    print("Your file is ready: final_study_guide.md")


if __name__ == "__main__":
    asyncio.run(generate_study_guide())