import asyncio

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from core.brain import brain


class BrowserUseSkill:
    name = "browser_use"
    description = "Autonomous browser for searching, navigating, and extracting web content safely."

    def __init__(self):
        self.browser = None
        self.context = None

    async def _init_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

    async def navigate(self, url):
        if not self.browser:
            await self._init_browser()

        page = await self.context.new_page()
        await stealth_async(page)

        print(f"Navigating to: {url}")
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            # Safety: No form interactions allowed here
            text = self._extract_clean_text(content)
            await page.close()
            return text
        except Exception as e:
            await page.close()
            return f"Navigation Error: {e}"

    def _extract_clean_text(self, html):
        soup = BeautifulSoup(html, "lxml")
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()

        text = soup.get_text(separator="\n")
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)

    def search_google(self, query):
        url = f"https://www.google.com/search?q={query}"
        return asyncio.run(self.navigate(url))

    def run(self, input_data, context):
        # Smart routing
        if input_data.startswith("http"):
            raw_text = asyncio.run(self.navigate(input_data))
        else:
            raw_text = self.search_google(input_data)

        # 4. Summarization via Ollama
        summary = brain.llama.chat(f"Summarize this web content in 5 key points:\n\n{raw_text[:5000]}")

        return {
            "summary": summary,
            "raw_length": len(raw_text),
            "source": input_data
        }

browser_use_skill = BrowserUseSkill()
