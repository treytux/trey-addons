###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class IrTranslationHelper(models.AbstractModel):
    _name = 'ir.translation.helper'
    _description = 'Translation Helper'

    CATEGORY_MODELS = {
        'product.category',
        'product.public.category',
    }

    def get_translatable_fields(self, model_name):
        if model_name not in self.env:
            return []
        model = self.env[model_name]
        translatable = []
        for field_name, field in model._fields.items():
            if model_name in self.CATEGORY_MODELS and field_name != 'name':
                continue
            if self._is_supported_translatable_field(model, field):
                translatable.append((field_name, field))
        return sorted(translatable, key=lambda x: x[0])

    def _is_supported_translatable_field(self, model, field):
        if not field.translate or field.compute:
            return False
        if field.type not in ('char', 'text', 'html'):
            return False
        if field.store:
            return True
        return bool(self._get_related_stored_field(model, field))

    def _get_related_stored_field(self, model, field):
        if not field.related:
            return False
        related_model = model
        related_field = field
        related_parts = field.related.split('.')
        for index, field_name in enumerate(related_parts):
            related_field = related_model._fields.get(field_name)
            if not related_field:
                return False
            if index < len(related_parts) - 1:
                if not related_field.comodel_name:
                    return False
                related_model = self.env[related_field.comodel_name]
        return related_field if related_field.store else False

    def _translation_exists(
            self, record, field, field_name, dest_lang, src_lang,
            source_text):
        trans_record, trans_field = self._get_translation_record_and_field(
            record, field)
        if not trans_record:
            return False, ''
        translations = trans_field._get_stored_translations(trans_record) or {}
        existing = translations.get(dest_lang, '')
        if dest_lang != src_lang and existing == source_text:
            return False, existing
        return existing and existing.strip(), existing

    def _get_translation_record_and_field(self, record, field):
        if field.store:
            return record, field
        if not field.related:
            return record.env[record._name], field
        related_path, field_name = field.related.rsplit('.', 1)
        related_record = record.mapped(related_path)
        if len(related_record) != 1:
            return record.env[related_record._name], field
        return related_record, related_record._fields[field_name]

    def _get_stored_translations(self, record, field):
        trans_record, trans_field = self._get_translation_record_and_field(
            record, field)
        if not trans_record:
            return {}
        return trans_field._get_stored_translations(trans_record) or {}

    @staticmethod
    def _has_translatable_content(field, value):
        if not value:
            return False
        if not isinstance(value, str):
            return bool(value)
        return bool(html2plaintext(value).strip())

    @staticmethod
    def _get_provider_language_codes(provider, src_lang, dest_lang):
        get_codes = getattr(provider, 'get_language_codes', None)
        if get_codes:
            return get_codes(src_lang, dest_lang)
        return src_lang.split('_')[0], dest_lang.split('_')[0]

    def _ensure_source_unchanged(
            self, record, field, field_name, src_lang, source_text):
        trans_record, trans_field = self._get_translation_record_and_field(
            record, field)
        if not trans_record:
            return
        trans_record.invalidate_recordset([trans_field.name])
        record.invalidate_recordset([field_name])
        current_source = getattr(record.with_context(lang=src_lang),
                                 field_name, '')
        if current_source != source_text:
            raise ValueError(
                f'Source language {src_lang} changed for {field_name}')

    def _ensure_source_translation(
            self, record, field, field_name, src_lang, source_text):
        if src_lang == 'en_US':
            return
        translations = self._get_stored_translations(record, field)
        if src_lang in translations:
            return
        trans_record, trans_field = self._get_translation_record_and_field(
            record, field)
        if not trans_record:
            return
        if callable(trans_field.translate):
            source_terms = trans_field.get_trans_terms(source_text)
            if not source_terms:
                return
            source_translation = {
                source_term: source_term
                for source_term in source_terms
            }
            trans_record.update_field_translations(trans_field.name, {
                src_lang: source_translation,
            })
        else:
            trans_record.update_field_translations(trans_field.name, {
                src_lang: source_text,
            })
        trans_record.invalidate_recordset([trans_field.name])
        record.invalidate_recordset([field_name])

    def _translate_field_for_record(
            self, record, field_name, dest_lang, provider, src_lang='en_US',
            overwrite=False):
        if dest_lang == src_lang:
            return {
                'success': False,
                'message': f'Source and target language are both {src_lang}, '
                           'skipping',
                'translated': '',
            }
        field = record._fields[field_name]
        trans_record, trans_field = self._get_translation_record_and_field(
            record, field)
        if not trans_record or not trans_field.store:
            return {
                'success': False,
                'message': _(
                    'Field %(field_name)s is not stored, skipping',
                    field_name=field_name),
                'translated': '',
            }
        src_record = record.with_context(lang=src_lang)
        source_text = getattr(src_record, field_name, '')
        if not self._has_translatable_content(field, source_text):
            return {
                'success': False,
                'message': f'Source text empty for {field_name}',
                'translated': '',
            }
        if not overwrite:
            exists, existing = self._translation_exists(
                record, field, field_name, dest_lang, src_lang, source_text
            )
            if exists:
                return {
                    'success': False,
                    'message': f'Translation exists for {field_name}, '
                               'skipping',
                    'translated': existing,
                }
        self._ensure_source_translation(
            record, field, field_name, src_lang, source_text
        )
        src_lang_code, dest_lang_code = self._get_provider_language_codes(
            provider, src_lang, dest_lang)
        if callable(field.translate):
            translated_text = self._translate_callable_field(
                record, field, field_name, source_text, dest_lang,
                provider, src_lang)
        else:
            translated_text = provider.translate(
                source_text, src_lang_code, dest_lang_code,
                html=field.type == 'html')
            record.update_field_translations(field_name, {
                dest_lang: translated_text,
            })
            record.invalidate_recordset([field_name])
            self._ensure_source_unchanged(
                record, field, field_name, src_lang, source_text)
        return {
            'success': True,
            'message': f'Translated {field_name}',
            'translated': translated_text,
        }

    def _translate_callable_field(
            self, record, field, field_name, source_text, dest_lang, provider,
            src_lang):
        src_lang_code, dest_lang_code = self._get_provider_language_codes(
            provider, src_lang, dest_lang)
        source_terms = field.get_trans_terms(source_text)
        if not source_terms:
            return source_text
        trans_record, trans_field = self._get_translation_record_and_field(
            record, field)
        translations = self._get_stored_translations(record, field)
        dest_source = translations.get(
            dest_lang, translations.get('en_US', source_text))
        dest_terms = trans_field.get_trans_terms(dest_source)
        if dest_terms:
            terms_to_replace = dest_terms
        else:
            terms_to_replace = source_terms
        translated_terms = {}
        for source_term, dest_term in zip(source_terms, terms_to_replace):
            translated_terms[dest_term] = provider.translate(
                source_term,
                src_lang_code,
                dest_lang_code,
                html=field.type == 'html')
        trans_record.with_context(
            lang=src_lang
        ).update_field_translations(trans_field.name, {
            dest_lang: translated_terms,
        })
        trans_record.invalidate_recordset([trans_field.name])
        record.invalidate_recordset([field_name])
        self._ensure_source_unchanged(
            record, field, field_name, src_lang, source_text)
        return getattr(record.with_context(lang=dest_lang), field_name, '')

    def translate_field_for_record(self, record, field_name, dest_lang,
                                   provider, src_lang='en_US', overwrite=False):
        try:
            with self.env.cr.savepoint():
                return self._translate_field_for_record(
                    record, field_name, dest_lang, provider,
                    src_lang=src_lang, overwrite=overwrite)
        except Exception as e:
            _logger.error(
                'Translation error for %s.%s (%s): %s',
                record._name, field_name, record.id, str(e)
            )
            return {
                'success': False,
                'message': f'Error translating {field_name}: {str(e)}',
                'translated': '',
            }

    def translate_records_batch(self, records, field_names, dest_lang,
                                provider, src_lang='en_US', overwrite=False):
        summary = {
            'total_records': len(records),
            'total_fields': len(field_names),
            'successful': 0,
            'skipped': 0,
            'errors': 0,
            'error_messages': [],
            'error_items': [],
        }
        for record in records:
            for field_name in field_names:
                result = self.translate_field_for_record(
                    record, field_name, dest_lang, provider, src_lang,
                    overwrite)
                if result['success']:
                    summary['successful'] += 1
                else:
                    if 'skipping' in result['message']:
                        summary['skipped'] += 1
                    else:
                        summary['errors'] += 1
                        summary['error_messages'].append(
                            f'{record.id}.{field_name}: '
                            f'{result["message"]}'
                        )
                        summary['error_items'].append({
                            'record_id': record.id,
                            'field_name': field_name,
                            'message': result['message'],
                        })
        return summary

    def record_needs_translation(
            self, record, field_names, target_langs, src_lang='en_US'):
        for field_name in field_names:
            field = record._fields.get(field_name)
            if not field or not field.translate or field.compute:
                continue
            trans_record, trans_field = self._get_translation_record_and_field(
                record, field)
            if not trans_record or not trans_field.store:
                continue
            translations = self._get_stored_translations(record, field)
            if src_lang != 'en_US' and src_lang not in translations:
                continue
            source_text = getattr(
                record.with_context(lang=src_lang), field_name, '')
            if not self._has_translatable_content(field, source_text):
                continue
            for target_lang in target_langs:
                if target_lang == src_lang:
                    continue
                existing = translations.get(target_lang)
                if not existing or existing == source_text:
                    return True
        return False

    def find_records_needing_translation(
            self, records, field_names, target_langs, src_lang='en_US'):
        return records.filtered(
            lambda record: self.record_needs_translation(
                record, field_names, target_langs, src_lang=src_lang))
