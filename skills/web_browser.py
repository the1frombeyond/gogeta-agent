import webbrowser

from skills.base import Skill


class BrowserSkill(Skill):
    name = "browser"
    description = "Opens and searches web"

    def run(self, input_data, context):
        # Extract search query or URL
        query = input_data.replace("search", "").replace("open", "").strip()
        if "." in query and " " not in query:
            url = query if query.startswith("http") else f"https://{query}"
        else:
            url = f"https://www.google.com/search?q={query}"

        webbrowser.open(url)
        return f"Searching for {query} or navigating to the requested URL."
