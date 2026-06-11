import json

from playwright.async_api import async_playwright


class AgentBrowser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts = {} # session_name -> context
        self.refs = {}     # ref_id -> element_handle

    async def _get_context(self, session="default"):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)

        if session not in self.contexts:
            self.contexts[session] = await self.browser.new_context()
        return self.contexts[session]

    async def open(self, url, session="default"):
        ctx = await self._get_context(session)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(url)
        return f"Opened {url}"

    async def snapshot(self, session="default"):
        ctx = await self._get_context(session)
        page = ctx.pages[0]
        # Simplified ref generation for demo
        elements = await page.query_selector_all("button, input, a, select")
        self.refs = {f"e{i}": el for i, el in enumerate(elements)}

        data = {
            "success": True,
            "data": {
                "refs": {rid: {"tag": await el.evaluate("e => e.tagName")} for rid, el in self.refs.items()}
            }
        }
        return json.dumps(data, indent=2)

    async def click(self, ref_id):
        if ref_id.startswith("@"): ref_id = ref_id[1:]  # noqa: E701
        el = self.refs.get(ref_id)
        if el:
            await el.click()
            return f"Clicked {ref_id}"
        return f"Error: Reference {ref_id} not found."

    async def fill(self, ref_id, text):
        if ref_id.startswith("@"): ref_id = ref_id[1:]  # noqa: E701
        el = self.refs.get(ref_id)
        if el:
            await el.fill(text)
            return f"Filled {ref_id} with {text}"
        return f"Error: Reference {ref_id} not found."

# Singleton instance
agent_browser = AgentBrowser()
