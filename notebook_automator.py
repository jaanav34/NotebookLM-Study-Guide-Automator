import asyncio
import re
from playwright.async_api import async_playwright, expect

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
            await page.wait_for_timeout(4000)  

            # 4) Pull absolutely everything
            raw = await ai_container.evaluate("node => node.textContent")

            # 5) Clean up UI bits & citations
            import re
            clean = re.sub(r"keep_pin.*", "", raw, flags=re.DOTALL)      # drop pin/copy/thumbs
            clean = re.sub(r"Save to note", "", clean)                    # drop note button text
            clean = re.sub(r"\[\d+\]", "", clean)                         # drop inline [1],[2] markers
            clean = re.sub(r"\s{2,}", " ", clean).strip()                 # collapse extra whitespace
            # raw_clean is your 'clean' string from before
            raw_clean = clean

            # 1. Ensure each top‑level bullet starts on its own line
            #    (we split on the “• ” marker, then re‑join with a newline + marker)
            sections = raw_clean.split("• ")
            formatted = "• " + "\n\n• ".join(s.strip() for s in sections if s.strip())

            # 2. Turn each sub‑bullet “◦ ” into an indented bullet
            formatted = formatted.replace("◦ ", "\n    ◦ ")

            # 3. Add a blank line after the introductory sentence(s)
            #    (optional: if you know where the break is, e.g. after “role:”)
            formatted = formatted.replace("role:", "role:\n")

            # 1) Remove trailing ellipses and stray numbers (like “3….” or “310.”)
            clean = re.sub(r"\d+\.\.\.+", "", formatted)

            # 2) Collapse any remaining runs of dots
            clean = re.sub(r"\.{2,}", ".", clean)

            # 3) Normalize whitespace around bullets
            #    Ensure every “•” is on its own line
            clean = re.sub(r"\s*•\s*", "\n\n• ", clean).strip()

            # 4) Normalize sub‑bullets “◦”
            #    Ensure they indent under the parent
            clean = re.sub(r"\s*◦\s*", "\n    ◦ ", clean)

            # 5) Tidy up multiple blank lines (max two)
            clean = re.sub(r"\n{3,}", "\n\n", clean)

            return clean or "Scraped text was empty."


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