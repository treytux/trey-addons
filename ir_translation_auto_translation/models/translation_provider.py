###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    @property
    @abstractmethod
    def code(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    def __init__(self, config):
        self.config = config or {}

    def get_language_codes(self, src_lang, dest_lang):
        return src_lang.split('_')[0], dest_lang.split('_')[0]

    @abstractmethod
    def translate(self, text, src_lang, dest_lang, html=False):
        pass

    def translate_batch(self, texts, src_lang, dest_lang, html=False):
        return [
            self.translate(text, src_lang, dest_lang, html)
            for text in texts
        ]
