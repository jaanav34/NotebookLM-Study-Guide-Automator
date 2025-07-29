import asyncio
import re
from playwright.async_api import async_playwright, expect #type: ignore

# --- Configuration ---
NOTEBOOK_URL = "https://notebooklm.google.com/notebook/" 

# --- DOM Selectors ---
CHAT_INPUT_SELECTOR = "textarea[placeholder*='Start typing…']"
RESPONSE_CONTAINER_SELECTOR = "div.to-user-container .message-text-content"

async def query_notebook(question: str) -> str:
    """
    Connects to a running Chrome instance, finds the NotebookLM tab,
    asks a question, and scrapes the response.
    """
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
        except Exception as e:
            return f"Error connecting to browser. Is it running with --remote-debugging-port=9222? Details: {e}"

        page = None
        for p_iter in context.pages:
            if p_iter.url.startswith(NOTEBOOK_URL):
                page = p_iter
                break
        
        if not page:
            return f"Error: No open tab found with a URL starting with '{NOTEBOOK_URL}'"
        
        print("Successfully connected to the NotebookLM tab.")

        try:
            chat_input = page.locator(CHAT_INPUT_SELECTOR)
            await expect(chat_input).to_be_visible(timeout=10000)
            
            initial_response_count = await page.locator(RESPONSE_CONTAINER_SELECTOR).count()

            await chat_input.fill(question)
            await chat_input.press("Enter")
            print(f"Asked question: '{question}'")

            await expect(page.locator(RESPONSE_CONTAINER_SELECTOR)).to_have_count(
                initial_response_count + 1, timeout=20000
            )
            print("New response detected.")

      # 1) wait for the input
            # 1) After detecting the new AI bubble…
            ai_container = page.locator("div.to-user-container").last

            # 2) Wait for the spinner/dots to disappear (i.e. streaming done)
            await expect(ai_container.locator(".loading-dots")).to_be_hidden(timeout=60000)

            # 3) (Optional) small buffer to let any final bits render
            await page.wait_for_timeout(15000)  
            # --- NEW: Save raw response as Markdown ---
            try:
                import html2text
                message_content = ai_container.locator(".message-text-content")
                html_content = await message_content.evaluate("node => node.innerHTML")

                h = html2text.HTML2Text()
                h.body_width = 0  # Don't wrap lines
                markdown_content = h.handle(html_content)

                # --- FINAL Markdown Cleaning ---
                # 1. Fix unicode characters
                markdown_content = markdown_content.replace('â€¢', '•')
                markdown_content = markdown_content.replace('â€¦', '…')

                # 2. Remove numbers attached to the end of words (e.g., "hallucination1")
                #    This is the key fix.
                markdown_content = re.sub(r'(\w)\d+\b', r'\1', markdown_content)
                markdown_content = re.sub(r'\.\.\.\.', '.', markdown_content)

                # 3. Remove any remaining bracketed citations like [1] or [2,3]
                markdown_content = re.sub(r"\[[\d,\s]+\]", "", markdown_content)
                
                with open("response.md", "w", encoding="utf-8") as f:
                    f.write(markdown_content.strip())
                print("Formatted Markdown response saved to response.md")

            except Exception as e:
                print(f"Could not save Markdown file: {e}")


            # 4) Pull absolutely everything
            # --- PRE-PROCESS HTML TO REMOVE CITATIONS ---
            # This JavaScript code runs inside the browser to remove both types of citation buttons.
            await ai_container.evaluate("""
                node => {
                    // Selects both numbered citations and the '...' expander button
                    const citations = node.querySelectorAll('button.citation-marker');
                    citations.forEach(el => el.remove());
                }
            """)

            # --- Save Cleaned Markdown ---
            # This part is for the final study guide file.
            markdown_content = ""
            try:
                import html2text
                message_content = ai_container.locator(".message-text-content")
                html_content = await message_content.evaluate("node => node.innerHTML")
                
                h = html2text.HTML2Text()
                h.body_width = 0
                markdown_content = h.handle(html_content)

                # Fix common unicode characters in the markdown output
                markdown_content = markdown_content.replace('â€¢', '•').replace('â€¦', '…')

                with open("response.md", "w", encoding="utf-8") as f:
                    f.write(markdown_content.strip())
                print("Cleaned Markdown response saved to response.md")

            except Exception as e:
                print(f"Could not save Markdown file: {e}")

            # --- Clean and Format Plain Text (for Terminal Display) ---
            # This part uses the SAFE regex rules to make the terminal output readable.
            raw_text = await ai_container.evaluate("node => node.textContent")
            
            # 1. Remove UI text like "Save to note", etc.
            clean_text = re.sub(r"keep_pin.*", "", raw_text, flags=re.DOTALL)
            clean_text = re.sub(r"Save to note", "", clean_text)

            # 2. Fix unicode characters and collapse whitespace
            clean_text = clean_text.replace('â€¢', '•').replace('â€¦', '…')
            clean_text = re.sub(r"\s{2,}", " ", clean_text).strip()

            # 3. Format for terminal readability
            clean_text = clean_text.replace("• ", "\n\n• ").strip()

            # --- Print the clean terminal text to the console ---
            # This is separate from the markdown file generation.
            print("\n--- Scraped Response (for Terminal) ---")
            print(clean_text)
            print("---------------------------------------")

            # The function's main purpose is to return clean markdown for the study guide generator.
            return markdown_content.strip() or "Scraped markdown was empty."

        except Exception as e:
            return f"An error occurred during automation: {e}"

async def main():
    my_question = "Summarize the key findings from the uploaded research paper."
    print("--- Starting NotebookLM Automator ---")
    response = await query_notebook(my_question)
    print("\n--- Scraped Response ---")
    print(response)
    print("--------------------------")

if __name__ == "__main__":
    asyncio.run(main())