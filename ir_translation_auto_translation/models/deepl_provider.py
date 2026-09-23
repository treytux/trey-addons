###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import time

import requests

from .translation_provider import TranslationProvider

_logger = logging.getLogger(__name__)


class DeepLProvider(TranslationProvider):
    code = 'deepl'
    name = 'DeepL'

    def __init__(self, config):
        super().__init__(config)
        self.api_key = (config.get('deepl_api_key') or '').strip()
        if not self.api_key:
            raise ValueError('DeepL API key is not configured')
        self.timeout = int(config.get('timeout', 10))
        self.retries = max(1, int(config.get('retries', 3)))
        self.sleep_ms = int(config.get('sleep_between_calls_ms', 100))
        self.base_url = (
            'https://api-free.deepl.com'
            if self.api_key.endswith(':fx')
            else 'https://api.deepl.com'
        )

    @staticmethod
    def _language_code(lang_code, target=False):
        parts = lang_code.replace('_', '-').upper().split('-')
        if target and parts[0] == 'EN' and len(parts) > 1:
            return f'EN-{parts[1]}'
        return parts[0]

    def get_language_codes(self, src_lang, dest_lang):
        return src_lang, dest_lang

    def translate(self, text, src_lang, dest_lang, html=False):
        if not text or not text.strip():
            return text
        payload = {
            'text': [text],
            'target_lang': self._language_code(dest_lang, target=True),
        }
        if src_lang:
            payload['source_lang'] = self._language_code(src_lang)
        if html:
            payload.update({
                'tag_handling': 'html',
                'tag_handling_version': 'v2',
            })
        headers = {
            'Authorization': f'DeepL-Auth-Key {self.api_key}',
            'Content-Type': 'application/json',
        }
        for attempt in range(self.retries):
            try:
                time.sleep(self.sleep_ms / 1000.0)
                response = requests.post(
                    f'{self.base_url}/v2/translate',
                    json=payload,
                    headers=headers,
                    timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                translations = data.get('translations') or []
                result = translations[0].get('text') if translations else None
                if not isinstance(result, str) or not result.strip():
                    raise RuntimeError('DeepL returned an invalid result')
                return result
            except Exception as exc:
                _logger.warning(
                    'Translation attempt %d/%d failed '
                    '[provider=%s, %s->%s]: %s',
                    attempt + 1, self.retries, self.code,
                    src_lang, dest_lang, exc)
                if attempt == self.retries - 1:
                    raise RuntimeError(
                        f'Translation failed after {self.retries} retries '
                        f'[{src_lang}->{dest_lang}]: {exc}'
                    ) from exc
                time.sleep((attempt + 1) * 0.5)

    def translate_batch(self, texts, src_lang, dest_lang, html=False):
        return [
            self.translate(text, src_lang, dest_lang, html=html)
            for text in texts
        ]
