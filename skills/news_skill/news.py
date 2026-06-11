import urllib.parse


class NewsAggregator:

    def _parse_feed(self, url):
        try:
            import feedparser
            feed = feedparser.parse(url)
            return [{'title': e.title, 'link': e.link,
                     'published': e.get('published', '')}
                    for e in feed.entries[:10]]
        except ImportError:
            return {'error': 'feedparser not available'}
        except Exception as e:
            return {'error': str(e)}

    def headlines(self, category=None, region=None):
        urls = {
            'world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
            'business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
            'science': 'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
            'health': 'http://feeds.bbci.co.uk/news/health/rss.xml',
        }
        url = urls.get(category, 'http://feeds.bbci.co.uk/news/rss.xml')
        return self._parse_feed(url)

    def search(self, keyword):
        url = ('https://news.google.com/rss/search?q='
               f'{urllib.parse.quote(keyword)}')
        return self._parse_feed(url)

    def summarize(self, url):
        return {'error': 'Summarization requires additional NLP libraries'}


def run(action, **kwargs):
    na = NewsAggregator()
    method = getattr(na, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
