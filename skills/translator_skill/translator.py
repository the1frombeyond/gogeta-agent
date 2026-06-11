class Translator:

    def __init__(self):
        self._gt = None
        try:
            from googletrans import Translator as GTranslator
            self._gt = GTranslator()
        except ImportError:
            pass

    def detect(self, text):
        if self._gt:
            try:
                d = self._gt.detect(text)
                return {'lang': d.lang, 'confidence': d.confidence}
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'googletrans not available'}

    def translate(self, text, target_lang, source_lang=None):
        if self._gt:
            try:
                kwargs = {'dest': target_lang}
                if source_lang:
                    kwargs['src'] = source_lang
                result = self._gt.translate(text, **kwargs)
                return {'text': result.text,
                        'source_lang': result.src,
                        'target_lang': result.dest}
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'googletrans not available'}

    def get_supported_languages(self):
        if self._gt:
            try:
                return self._gt.languages
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'googletrans not available'}


def run(action, **kwargs):
    t = Translator()
    method = getattr(t, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
