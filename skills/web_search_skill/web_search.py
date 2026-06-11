from skills.browser_use_skill.browser_use import browser_use_skill


class WebSearchSkill:
    name = "web_search"
    description = "Quick web search for snippets and facts."

    def run(self, query, context):
        print(f"Performing quick search for: {query}")
        result = browser_use_skill.search_google(query)
        # We just want a quick summary from the search result page
        return result

web_search = WebSearchSkill()
