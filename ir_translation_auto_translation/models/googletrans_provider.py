###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import time

from lxml import etree
from lxml import html as lxml_html

try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATOR_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATOR_AVAILABLE = False

from .translation_provider import TranslationProvider

_logger = logging.getLogger(__name__)

LANG_CODE_MAP = {
    'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', 'ar': 'arabic',
    'hy': 'armenian', 'as': 'assamese', 'ay': 'aymara',
    'az': 'azerbaijani', 'bm': 'bambara', 'eu': 'basque',
    'be': 'belarusian', 'bn': 'bengali', 'bh': 'bihari',
    'bi': 'bislama', 'bs': 'bosnian', 'bg': 'bulgarian',
    'ca': 'catalan', 'ceb': 'cebuano', 'ny': 'chichewa',
    'zh': 'chinese simplified', 'co': 'corsican', 'hr': 'croatian',
    'cs': 'czech', 'da': 'danish', 'nl': 'dutch', 'en': 'english',
    'eo': 'esperanto', 'et': 'estonian', 'tl': 'filipino',
    'fi': 'finnish', 'fr': 'french', 'fy': 'frisian',
    'gl': 'galician', 'ka': 'georgian', 'de': 'german',
    'el': 'greek', 'gn': 'guarani', 'gu': 'gujarati',
    'ht': 'haitian creole', 'ha': 'hausa', 'haw': 'hawaiian',
    'he': 'hebrew', 'hi': 'hindi', 'hmn': 'hmong',
    'hu': 'hungarian', 'is': 'icelandic', 'ig': 'igbo',
    'id': 'indonesian', 'ia': 'interlingua',
    'ie': 'interlingue', 'iu': 'inuktitut', 'ik': 'inupiak',
    'ga': 'irish', 'it': 'italian', 'ja': 'japanese',
    'jw': 'javanese', 'kn': 'kannada', 'kk': 'kazakh',
    'km': 'khmer', 'rw': 'kinyarwanda', 'ky': 'kirghiz',
    'ko': 'korean', 'ku': 'kurdish', 'lo': 'laothian',
    'la': 'latin', 'lv': 'latvian', 'ln': 'lingala',
    'lt': 'lithuanian', 'lb': 'luxembourgish', 'mk': 'macedonian',
    'mg': 'malagasy', 'ms': 'malay', 'ml': 'malayalam',
    'mt': 'maltese', 'mi': 'maori', 'mr': 'marathi',
    'mn': 'mongolian', 'my': 'myanmar', 'ne': 'nepali',
    'no': 'norwegian', 'or': 'odia', 'ps': 'pashto',
    'fa': 'persian', 'pl': 'polish', 'pt': 'portuguese',
    'pa': 'punjabi', 'qu': 'quechua', 'ro': 'romanian',
    'ru': 'russian', 'sm': 'samoan', 'sg': 'sango',
    'sa': 'sanskrit', 'gd': 'scots gaelic', 'sr': 'serbian',
    'st': 'sesotho', 'tn': 'setswana', 'sn': 'shona',
    'sd': 'sindhi', 'si': 'sinhala', 'sk': 'slovak',
    'sl': 'slovenian', 'so': 'somali', 'es': 'spanish',
    'su': 'sundanese', 'sw': 'swahili', 'sv': 'swedish',
    'tg': 'tajik', 'ta': 'tamil', 'tt': 'tatar', 'te': 'telugu',
    'th': 'thai', 'bo': 'tibetan', 'ti': 'tigrinya',
    'to': 'tongan', 'tr': 'turkish', 'tk': 'turkmen',
    'tw': 'twi', 'uk': 'ukrainian', 'ur': 'urdu', 'ug': 'uighur',
    'uz': 'uzbek', 'vi': 'vietnamese', 'cy': 'welsh', 'wo': 'wolof',
    'xh': 'xhosa', 'yi': 'yiddish', 'yo': 'yoruba', 'za': 'zhuang',
    'zu': 'zulu',
}


class GoogletransProvider(TranslationProvider):
    code = 'googletrans'
    name = 'Google Translate (via deep-translator)'

    def __init__(self, config):
        super().__init__(config)
        if not GOOGLE_TRANSLATOR_AVAILABLE:
            raise ImportError(
                'Google Translate library not found. '
                'Install: pip install deep-translator>=1.11.0'
            )
        self.timeout = int(config.get('timeout', 10))
        self.retries = max(1, int(config.get('retries', 3)))
        self.sleep_ms = int(config.get('sleep_between_calls_ms', 100))

    @staticmethod
    def _get_lang_name(lang_code):
        lang_name = LANG_CODE_MAP.get(lang_code.lower(), None)
        if not lang_name:
            _logger.warning('Unknown language code: %s, using as-is', lang_code)
            return lang_code
        return lang_name

    def _create_translator(self, src_lang, dest_lang):
        return GoogleTranslator(
            source=self._get_lang_name(src_lang),
            target=self._get_lang_name(dest_lang),
            timeout=self.timeout)

    def translate(self, text, src_lang, dest_lang, html=False):
        if not text or not text.strip():
            return text
        if html:
            return self._translate_html(text, src_lang, dest_lang)
        return self._translate_plain(text, src_lang, dest_lang)

    def _translate_plain(self, text, src_lang, dest_lang):
        for attempt in range(self.retries):
            try:
                time.sleep(self.sleep_ms / 1000.0)
                translator = self._create_translator(src_lang, dest_lang)
                result = translator.translate(text)
                if not isinstance(result, str) or not result.strip():
                    raise RuntimeError(
                        'Translation provider returned an invalid result')
                return result
            except Exception as e:
                _logger.warning(
                    'Translation attempt %d/%d failed '
                    '[provider=%s, %s->%s]: %s',
                    attempt + 1, self.retries, self.code,
                    src_lang, dest_lang, str(e))
                if attempt == self.retries - 1:
                    _logger.error(
                        'Translation failed after %d retries '
                        '[provider=%s, %s->%s]: %s',
                        self.retries, self.code, src_lang, dest_lang,
                        str(e))
                    raise RuntimeError(
                        f'Translation failed after {self.retries} retries '
                        f'[{src_lang}->{dest_lang}]') from e
                time.sleep((attempt + 1) * 0.5)
        raise RuntimeError(
            f'Translation failed [{src_lang}->{dest_lang}]')

    def _translate_html(self, text, src_lang, dest_lang):
        try:
            wrapper = lxml_html.fragment_fromstring(
                text, create_parent='div')
            if wrapper.text and wrapper.text.strip():
                wrapper.text = self._translate_plain(
                    wrapper.text, src_lang, dest_lang)
            for element in wrapper.iterdescendants():
                if element.text and element.text.strip():
                    element.text = self._translate_plain(
                        element.text, src_lang, dest_lang)
                if element.tail and element.tail.strip():
                    element.tail = self._translate_plain(
                        element.tail, src_lang, dest_lang)
            return ''.join(
                etree.tostring(child, encoding='unicode')
                for child in wrapper)
        except Exception:
            _logger.exception('HTML translation failed')
            raise

    def translate_batch(self, texts, src_lang, dest_lang, html=False):
        return [
            self.translate(text, src_lang, dest_lang, html=html)
            for text in texts
        ]
