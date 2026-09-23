###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import time

from .translation_provider import TranslationProvider

_logger = logging.getLogger(__name__)


class DeepTranslatorBaseProvider(TranslationProvider):

    TRANSLATOR_CLASS = None

    def __init__(self, config):
        super().__init__(config)
        if not self.TRANSLATOR_CLASS:
            raise NotImplementedError(
                'TRANSLATOR_CLASS must be defined by subclass')
        self.timeout = int(config.get('timeout', 10))
        self.retries = int(config.get('retries', 3))
        self.sleep_ms = int(config.get('sleep_between_calls_ms', 100))

    def _create_translator(self, src_lang, dest_lang):
        try:
            return self.TRANSLATOR_CLASS(source=src_lang, target=dest_lang)
        except Exception as e:
            _logger.error('Failed to create translator: %s', str(e))
            raise

    def translate(self, text, src_lang, dest_lang, html=False):
        if not text or not text.strip():
            return text
        for attempt in range(self.retries):
            try:
                time.sleep(self.sleep_ms / 1000.0)
                translator = self._create_translator(src_lang, dest_lang)
                result = translator.translate(text)
                return result if isinstance(result, str) else text
            except Exception as e:
                _logger.warning(
                    'Translation attempt %d/%d failed for [%s->%s]: %s',
                    attempt + 1, self.retries, src_lang, dest_lang, str(e))
                if attempt == self.retries - 1:
                    _logger.error(
                        'Translation failed after %d retries: %s',
                        self.retries, str(e))
                    return text
                time.sleep((attempt + 1) * 0.5)
        return text

    def translate_batch(self, texts, src_lang, dest_lang, html=False):
        batch_size = int(self.config.get('batch_size_chars', 5000))
        result = []
        current_batch = []
        current_size = 0
        translator = self._create_translator(src_lang, dest_lang)
        for text in texts:
            text_len = len(text) if text else 0
            if text_len > batch_size:
                if current_batch:
                    batch_results = [
                        translator.translate(t) for t in current_batch
                    ]
                    result.extend(batch_results)
                    current_batch = []
                    current_size = 0
                try:
                    translated = translator.translate(text)
                    result.append(translated)
                except Exception:
                    result.append(text)
            elif current_size + text_len > batch_size:
                batch_results = [
                    translator.translate(t) for t in current_batch
                ]
                result.extend(batch_results)
                current_batch = [text]
                current_size = text_len
            else:
                current_batch.append(text)
                current_size += text_len
        if current_batch:
            batch_results = [translator.translate(t) for t in current_batch]
            result.extend(batch_results)
        return result
