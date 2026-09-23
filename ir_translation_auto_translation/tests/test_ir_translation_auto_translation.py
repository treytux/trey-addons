###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.deepl_provider import DeepLProvider
from ..models.googletrans_provider import GoogletransProvider


class MockTranslationProvider:
    code = 'mock'
    name = 'Mock Provider'

    def __init__(self, config):
        self.config = config

    def translate(self, text, src_lang, dest_lang, html=False):
        if not text:
            return text
        return f'{text} [{dest_lang}]'

    def translate_batch(self, texts, src_lang, dest_lang, html=False):
        return [
            self.translate(text, src_lang, dest_lang, html)
            for text in texts
        ]


class FailingTranslationProvider:
    code = 'failing'
    name = 'Failing Provider'

    def __init__(self, config):
        self.config = config

    def translate(self, text, src_lang, dest_lang, html=False):
        raise Exception('Translation service unavailable')

    def translate_batch(self, texts, src_lang, dest_lang, html=False):
        raise Exception('Translation service unavailable')


class SourceMutatingProvider(MockTranslationProvider):

    def __init__(self, config, record, field_name, src_lang, source_value):
        super().__init__(config)
        self.record = record
        self.field_name = field_name
        self.src_lang = src_lang
        self.source_value = source_value
        self.mutated = False

    def translate(self, text, src_lang, dest_lang, html=False):
        if not self.mutated:
            self.mutated = True
            self.record.with_context(lang=self.src_lang).write({
                self.field_name: self.source_value,
            })
        return super().translate(text, src_lang, dest_lang, html)


class BaseTranslationTest(TransactionCase):
    MODEL = 'product.template'
    FIELD = 'name'
    SRC_LANG = 'en_US'
    DEST_LANG = 'es_ES'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_lang_installed('es_ES')
        cls._ensure_lang_installed('de_DE')

    @classmethod
    def _ensure_lang_installed(cls, code):
        lang_model = cls.env['res.lang'].with_context(active_test=False)
        lang = lang_model._activate_lang(code)
        if not lang:
            lang = lang_model._create_lang(code)
        lang.active = True
        return lang

    def setUp(self):
        super().setUp()
        self.mock_provider = MockTranslationProvider({})
        self.failing_provider = FailingTranslationProvider({})

    def _get_language(self, code):
        return self._ensure_lang_installed(code)

    def _get_model_field(self, model_name, field_name):
        field = self.env['ir.model.fields'].search(
            [('model', '=', model_name), ('name', '=', field_name)],
            limit=1
        )
        if not field:
            self.skipTest(f'Field {model_name}.{field_name} not found')
        return field

    def _get_product_values(self, name, extra_vals=None):
        vals = {'name': name}
        product_model = self.env['product.template']
        if 'sale_line_warn' in product_model._fields:
            vals['sale_line_warn'] = 'no-message'
        if 'purchase_line_warn' in product_model._fields:
            vals['purchase_line_warn'] = 'no-message'
        if 'base_unit_count' in product_model._fields:
            vals['base_unit_count'] = 0.0
        if extra_vals:
            vals.update(extra_vals)
        return vals

    def _create_product(self, name='Test Product', extra_vals=None):
        return self.env['product.template'].create(
            self._get_product_values(name, extra_vals))

    def _create_products(self, count=3):
        return self.env['product.template'].create([
            self._get_product_values(f'Product {i}') for i in range(count)
        ])

    def _create_website_page(
            self, arch_db='<div><p>Page body text</p></div>',
            lang=None):
        view_model = self.env['ir.ui.view']
        if lang:
            view_model = view_model.with_context(lang=lang)
        view = view_model.create({
            'name': 'Translation Test Page View',
            'type': 'qweb',
            'arch_db': arch_db,
        })
        return self.env['website.page'].create({
            'url': '/translation-test-page',
            'view_id': view.id,
        })

    def _translate_field(self, record, field, dest_lang, provider,
                         src_lang=SRC_LANG, overwrite=False):
        return self.env['ir.translation.helper'].translate_field_for_record(
            record, field, dest_lang, provider, src_lang=src_lang,
            overwrite=overwrite)

    def _translate_batch(self, records, fields, dest_lang, provider,
                         src_lang=SRC_LANG, overwrite=False):
        return self.env['ir.translation.helper'].translate_records_batch(
            records, fields, dest_lang, provider, src_lang=src_lang,
            overwrite=overwrite
        )


class TestTranslationHelper(BaseTranslationTest):
    def setUp(self):
        super().setUp()
        self.helper = self.env['ir.translation.helper']

    def test_get_translatable_fields_product_template(self):
        fields = self.helper.get_translatable_fields(self.MODEL)
        self.assertIsInstance(fields, list)
        field_names = [f[0] for f in fields]
        self.assertIn(self.FIELD, field_names)

    def test_get_translatable_fields_skips_non_stored_fields(self):
        fields = self.helper.get_translatable_fields(self.MODEL)
        field_names = [f[0] for f in fields]
        self.assertNotIn('website_name', field_names)

    def test_get_translatable_fields_invalid_model(self):
        fields = self.helper.get_translatable_fields('nonexistent.model')
        self.assertEqual(fields, [])

    def test_category_translatable_fields_only_include_name(self):
        for model_name in (
                'product.category', 'product.public.category'):
            fields = self.helper.get_translatable_fields(model_name)
            field_names = [field_name for field_name, field in fields]
            self.assertEqual(field_names, ['name'])

    def test_get_translatable_fields_sorted(self):
        fields = self.helper.get_translatable_fields(self.MODEL)
        field_names = [f[0] for f in fields]
        self.assertEqual(field_names, sorted(field_names))

    def test_translate_field_empty_source(self):
        product = self._create_product()
        product.with_context(lang=self.SRC_LANG).write({self.FIELD: ''})
        result = self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.mock_provider)
        self.assertFalse(result['success'])
        self.assertIn('empty', result['message'].lower())

    def test_translate_field_whitespace_source(self):
        product = self._create_product()
        product.with_context(lang=self.SRC_LANG).write({self.FIELD: '   '})
        result = self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.mock_provider)
        self.assertFalse(result['success'])
        self.assertIn('empty', result['message'].lower())

    def test_translate_field_success(self):
        product = self._create_product('Product for success test')
        result = self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.mock_provider,
            overwrite=True)
        self.assertTrue(result['success'])
        translated = product.with_context(lang=self.DEST_LANG).name
        self.assertIn('[es]', translated)
        self.assertEqual(result['translated'], translated)

    def test_translate_field_skip_existing(self):
        product = self._create_product()
        existing_trans = 'Producto Existente'
        product.with_context(lang=self.DEST_LANG).write({
            self.FIELD: existing_trans,
        })
        result = self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.mock_provider,
            overwrite=False)
        self.assertFalse(result['success'])
        self.assertIn('skipping', result['message'].lower())
        self.assertEqual(
            product.with_context(lang=self.DEST_LANG).name,
            existing_trans)

    def test_translate_field_overwrite_existing(self):
        product = self._create_product('Product for overwrite test')
        old_translation = 'Producto Viejo Manual'
        product.with_context(lang=self.DEST_LANG).write({
            self.FIELD: old_translation,
        })
        product.invalidate_recordset([self.FIELD])
        result = self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.mock_provider,
            overwrite=True
        )
        self.assertTrue(result['success'])
        product.invalidate_recordset([self.FIELD])
        translated = product.with_context(lang=self.DEST_LANG).name
        self.assertIn('[es]', translated)
        self.assertNotEqual(translated, old_translation)

    def test_translate_field_keeps_source_language(self):
        self._get_language('es_ES')
        product = self.env['product.template'].with_context(
            lang='es_ES'
        ).create(self._get_product_values('Nombre fuente'))
        source_before = product.with_context(lang='es_ES').name
        result = self._translate_field(
            product, self.FIELD, 'en_US', self.mock_provider,
            src_lang='es_ES', overwrite=False)
        self.assertTrue(result['success'])
        product.invalidate_recordset([self.FIELD])
        self.assertEqual(
            product.with_context(lang='es_ES').name, source_before)
        self.assertIn('[en]', product.with_context(lang='en_US').name)

    def test_translate_field_keeps_source_for_multiple_targets(self):
        self._get_language('es_ES')
        self._get_language('de_DE')
        product = self.env['product.template'].with_context(
            lang='es_ES'
        ).create(self._get_product_values('Nombre multilenguaje'))
        source_before = product.with_context(lang='es_ES').name
        for dest_lang in ('en_US', 'de_DE'):
            result = self._translate_field(
                product, self.FIELD, dest_lang, self.mock_provider,
                src_lang='es_ES', overwrite=False)
            self.assertTrue(result['success'])
        product.invalidate_recordset([self.FIELD])
        self.assertEqual(
            product.with_context(lang='es_ES').name, source_before)
        self.assertIn('[en]', product.with_context(lang='en_US').name)
        self.assertIn('[de]', product.with_context(lang='de_DE').name)

    def test_translate_field_skip_same_source_and_target(self):
        product = self._create_product('Product for same language test')
        source_before = product.with_context(lang=self.SRC_LANG).name
        result = self._translate_field(
            product, self.FIELD, self.SRC_LANG, self.mock_provider,
            src_lang=self.SRC_LANG, overwrite=True)
        self.assertFalse(result['success'])
        self.assertIn('skipping', result['message'].lower())
        self.assertEqual(
            product.with_context(lang=self.SRC_LANG).name, source_before)

    def test_translate_field_different_language_codes(self):
        product = self._create_product('Product for french test')
        self._get_language('de_DE')
        dest_lang = 'de_DE'
        result = self._translate_field(
            product, self.FIELD, dest_lang, self.mock_provider,
            overwrite=True
        )
        self.assertTrue(result['success'])
        self.assertIn('[de]', result['translated'])

    def test_translate_field_provider_exception(self):
        product = self._create_product('Product for exception test')
        result = self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.failing_provider,
            overwrite=True
        )
        self.assertFalse(result['success'])
        msg_lower = result['message'].lower()
        self.assertTrue(
            'error' in msg_lower or 'exception' in msg_lower or 'unavailable'
            in msg_lower,
            f"Expected error message but got: {result['message']}"
        )

    def test_find_records_needing_translation_for_missing_language(self):
        product = self._create_product('Product with missing translation')
        records = self.helper.find_records_needing_translation(
            product, [self.FIELD], [self.DEST_LANG], src_lang=self.SRC_LANG
        )
        self.assertEqual(records, product)

    def test_find_records_ignores_empty_html_fields(self):
        if 'warranty' not in self.env['product.template']._fields:
            self.skipTest('Field product.template.warranty not found')
        product = self._create_product(
            'Product with empty warranty',
            {'warranty': '<p><br></p>'})
        records = self.helper.find_records_needing_translation(
            product, ['warranty'], [self.DEST_LANG], src_lang=self.SRC_LANG)
        self.assertFalse(records)

    def test_find_records_needing_translation_ignores_completed_language(self):
        product = self._create_product('Product with completed translation')
        self._translate_field(
            product, self.FIELD, self.DEST_LANG, self.mock_provider,
            overwrite=True)
        records = self.helper.find_records_needing_translation(
            product, [self.FIELD], [self.DEST_LANG], src_lang=self.SRC_LANG)
        self.assertFalse(records)

    def test_find_records_requires_explicit_non_base_source_language(self):
        product = self._create_product('Product with fallback source only')
        records = self.helper.find_records_needing_translation(
            product, [self.FIELD], [self.DEST_LANG], src_lang='es_ES')
        self.assertFalse(records)

    def test_find_records_needing_translation_detects_source_copy(self):
        product = self._create_product('Product with source copy')
        product.with_context(lang=self.DEST_LANG).write({
            self.FIELD: product.with_context(lang=self.SRC_LANG).name,
        })
        records = self.helper.find_records_needing_translation(
            product, [self.FIELD], [self.DEST_LANG], src_lang=self.SRC_LANG)
        self.assertEqual(records, product)

    def test_translate_records_batch_success(self):
        products = self.env['product.template'].create([
            self._get_product_values('Batch Product A'),
            self._get_product_values('Batch Product B'),
        ])
        summary = self._translate_batch(
            products, [self.FIELD], self.DEST_LANG, self.mock_provider,
            overwrite=True
        )
        self.assertEqual(summary['successful'], 2)
        self.assertEqual(summary['errors'], 0)
        self.assertEqual(summary['skipped'], 0)
        self.assertEqual(summary['total_records'], 2)
        self.assertEqual(summary['total_fields'], 1)

    def test_translate_records_batch_multiple_fields(self):
        self._get_language(self.DEST_LANG)
        product = self._create_product('Multi Field Product', {
            'description': 'Multi Field Description',
        })
        summary = self._translate_batch(
            product, [self.FIELD, 'description'],
            self.DEST_LANG, self.mock_provider,
            overwrite=True
        )
        self.assertEqual(summary['successful'], 2)
        self.assertEqual(summary['total_fields'], 2)

    def test_translate_records_batch_mixed_results(self):
        products = self.env['product.template'].create([
            self._get_product_values('Mixed Batch Product 1'),
            self._get_product_values('Mixed Batch Product 2'),
        ])
        products[1].with_context(lang=self.DEST_LANG).write({
            self.FIELD: 'Producto Manual Existente',
        })
        summary = self._translate_batch(
            products, [self.FIELD], self.DEST_LANG,
            self.mock_provider, overwrite=False
        )
        self.assertEqual(summary['successful'], 1)
        self.assertEqual(summary['skipped'], 1)
        self.assertEqual(summary['errors'], 0)

    def test_translate_records_batch_with_errors(self):
        product = self._create_product('Error Batch Product')
        summary = self._translate_batch(
            product, [self.FIELD], self.DEST_LANG,
            self.failing_provider, overwrite=True
        )
        self.assertEqual(summary['successful'], 0)
        self.assertEqual(summary['errors'], 1)
        self.assertTrue(len(summary['error_messages']) > 0)
        self.assertEqual(len(summary['error_items']), 1)
        self.assertEqual(
            summary['error_items'][0]['record_id'], product.id)
        self.assertEqual(
            summary['error_items'][0]['field_name'], self.FIELD)

    def test_translate_records_batch_empty(self):
        empty = self.env['product.template']
        summary = self._translate_batch(
            empty, [self.FIELD], self.DEST_LANG, self.mock_provider)
        self.assertEqual(summary['total_records'], 0)
        self.assertEqual(summary['successful'], 0)

    def test_translate_records_batch_summary_counts(self):
        products = self._create_products(5)
        summary = self._translate_batch(
            products, [self.FIELD], self.DEST_LANG, self.mock_provider
        )
        total = summary['successful'] + summary['skipped'] + summary['errors']
        expected = summary['total_records'] * summary['total_fields']
        self.assertEqual(total, expected)


@tagged('post_install', '-at_install')
class TestCallableHtmlTranslation(BaseTranslationTest):

    def _skip_missing_product_field(self, field_name):
        if field_name not in self.env['product.template']._fields:
            self.skipTest(f'Field product.template.{field_name} not found')

    def test_translate_callable_html_keeps_source_language(self):
        source_arch = '<div><p>Descripcion del sitio web</p></div>'
        page = self._create_website_page(source_arch, lang='es_ES')
        result = self._translate_field(
            page, 'arch_db', 'en_US', self.mock_provider,
            src_lang='es_ES', overwrite=True)
        self.assertTrue(result['success'])
        page.invalidate_recordset(['arch_db'])
        english_arch = page.with_context(lang='en_US').arch_db
        spanish_arch = page.with_context(lang='es_ES').arch_db
        self.assertIn('[en]', english_arch)
        self.assertEqual(
            spanish_arch, source_arch)

    def test_translate_callable_html_rolls_back_source_mutation(self):
        source_arch = '<div><p>Descripcion del sitio web</p></div>'
        page = self._create_website_page(source_arch, lang='es_ES')
        provider = SourceMutatingProvider(
            {}, page, 'arch_db', 'es_ES',
            '<div><p>Origen alterado</p></div>')
        result = self._translate_field(
            page, 'arch_db', 'en_US', provider,
            src_lang='es_ES', overwrite=True)
        self.assertFalse(result['success'])
        self.assertIn('source language', result['message'].lower())
        page.invalidate_recordset(['arch_db'])
        self.assertEqual(
            page.with_context(lang='es_ES').arch_db,
            source_arch)
        self.assertEqual(
            page.with_context(lang='en_US').arch_db,
            source_arch)

    def test_translate_callable_html_skip_existing_translation(self):
        source_arch = '<div><p>Descripcion del sitio web</p></div>'
        page = self._create_website_page(source_arch, lang='es_ES')
        field = page.view_id._fields['arch_db']
        terms = field.get_trans_terms(source_arch)
        page.view_id.update_field_translations(
            'arch_db', {'en_US': {terms[0]: 'Manual website description'}})
        result = self._translate_field(
            page, 'arch_db', 'en_US', self.mock_provider,
            src_lang='es_ES', overwrite=False)
        self.assertFalse(result['success'])
        self.assertIn('skipping', result['message'].lower())
        self.assertEqual(
            page.with_context(lang='en_US').arch_db,
            '<div><p>Manual website description</p></div>')

    def test_translate_related_callable_page_arch_db(self):
        self._get_language('es_ES')
        page = self._create_website_page()
        field = page._fields['arch_db']
        self.assertTrue(callable(field.translate))
        self.assertTrue(field.related)
        summary = self._translate_batch(
            page, ['arch_db'], 'es_ES', self.mock_provider,
            src_lang='en_US', overwrite=True)
        self.assertEqual(summary['successful'], 1)
        self.assertEqual(summary['errors'], 0)
        page.invalidate_recordset(['arch_db'])
        spanish_arch = page.with_context(lang='es_ES').arch_db
        english_arch = page.with_context(lang='en_US').arch_db
        self.assertIn('Page body text [es]', spanish_arch)
        self.assertNotIn('[es]', english_arch)

    def test_translate_related_callable_page_arch_db_keeps_source(self):
        self._get_language('es_ES')
        source_arch = '<div><p>Texto fuente pagina</p></div>'
        page = self._create_website_page(source_arch, lang='es_ES')
        source_before = page.with_context(lang='es_ES').arch_db
        result = self._translate_field(
            page, 'arch_db', 'en_US', self.mock_provider,
            src_lang='es_ES', overwrite=False)
        self.assertTrue(result['success'])
        page.invalidate_recordset(['arch_db'])
        self.assertEqual(page.with_context(lang='es_ES').arch_db,
                         source_before)
        self.assertIn('Texto fuente pagina [en]',
                      page.with_context(lang='en_US').arch_db)

    def test_translate_product_website_description_from_fallback_source(self):
        self._skip_missing_product_field('website_description')
        source_html = '<p>Descripcion larga del sitio web</p>'
        product = self.env['product.template'].with_context(
            lang='es_ES'
        ).create(self._get_product_values('Producto descripcion web', {
            'website_description': source_html,
        }))
        result = self._translate_field(
            product, 'website_description', 'en_US', self.mock_provider,
            src_lang='es_ES', overwrite=True)
        self.assertTrue(result['success'], result['message'])
        product.invalidate_recordset(['website_description'])
        english_html = product.with_context(lang='en_US').website_description
        spanish_html = product.with_context(lang='es_ES').website_description
        self.assertIn('[en]', english_html)
        self.assertEqual(spanish_html, source_html)

    def test_translate_product_warranty_from_fallback_source(self):
        self._skip_missing_product_field('warranty')
        source_html = '<p>Garantia del producto</p>'
        product = self.env['product.template'].with_context(
            lang='es_ES'
        ).create(self._get_product_values('Producto garantia', {
            'warranty': source_html,
        }))
        result = self._translate_field(
            product, 'warranty', 'en_US', self.mock_provider,
            src_lang='es_ES', overwrite=True)
        self.assertTrue(result['success'], result['message'])
        product.invalidate_recordset(['warranty'])
        english_html = product.with_context(lang='en_US').warranty
        spanish_html = product.with_context(lang='es_ES').warranty
        self.assertIn('[en]', english_html)
        self.assertEqual(spanish_html, source_html)

    def test_translate_product_warranty_with_deepl_uses_regional_codes(self):
        self._skip_missing_product_field('warranty')
        source_html = '<p>Garantía del producto</p>'
        product = self.env['product.template'].with_context(
            lang='es_ES'
        ).create(self._get_product_values('Producto garantía', {
            'warranty': source_html,
        }))
        provider = DeepLProvider({
            'deepl_api_key': 'test-key:fx',
            'retries': 1,
            'sleep_between_calls_ms': 0,
        })
        response = type('Response', (), {
            'raise_for_status': lambda self: None,
            'json': lambda self: {
                'translations': [{'text': '<p>Product warranty</p>'}],
            },
        })()
        with patch(
                'odoo.addons.ir_translation_auto_translation.models.'
                'deepl_provider.requests.post', return_value=response) as post:
            result = self._translate_field(
                product, 'warranty', 'en_US', provider, src_lang='es_ES',
                overwrite=True)
        self.assertTrue(result['success'], result['message'])
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['source_lang'], 'ES')
        self.assertEqual(payload['target_lang'], 'EN-US')
        self.assertEqual(payload['tag_handling'], 'html')
        product.invalidate_recordset(['warranty'])
        self.assertEqual(
            product.with_context(lang='en_US').warranty,
            '<p>Product warranty</p>')
        self.assertEqual(
            product.with_context(lang='es_ES').warranty,
            source_html)


class TestResConfigSettings(BaseTranslationTest):
    def setUp(self):
        super().setUp()
        self.config = self.env['res.config.settings'].sudo()

    def test_get_translation_config(self):
        config_dict = self.config._get_translation_config()
        self.assertIn('timeout', config_dict)
        self.assertIn('retries', config_dict)
        self.assertIn('batch_size_chars', config_dict)
        self.assertIn('sleep_between_calls_ms', config_dict)

    def test_get_translation_provider(self):
        provider = self.config.get_translation_provider()
        self.assertIsNotNone(provider)
        self.assertEqual(provider.code, 'googletrans')

    def test_translation_config_defaults(self):
        config_dict = self.config._get_translation_config()
        self.assertEqual(config_dict['timeout'], '10')
        self.assertEqual(config_dict['retries'], '3')
        self.assertEqual(config_dict['batch_size_chars'], '5000')
        self.assertEqual(config_dict['sleep_between_calls_ms'], '100')


class TestGoogletransProvider(BaseTranslationTest):

    def test_translate_raises_after_retries_instead_of_returning_source(self):
        provider = GoogletransProvider({
            'retries': 2,
            'sleep_between_calls_ms': 0,
            'timeout': 1,
        })
        with patch(
                'odoo.addons.ir_translation_auto_translation.models.'
                'googletrans_provider.GoogleTranslator') as translator_class:
            translator_class.return_value.translate.side_effect = (
                RuntimeError('service unavailable'))
            with self.assertRaises(RuntimeError):
                provider.translate('Source text', 'en', 'es')
            self.assertEqual(translator_class.call_count, 2)

    def test_translate_batch_propagates_failures(self):
        provider = GoogletransProvider({
            'retries': 1,
            'sleep_between_calls_ms': 0,
            'timeout': 1,
        })
        with patch(
                'odoo.addons.ir_translation_auto_translation.models.'
                'googletrans_provider.GoogleTranslator') as translator_class:
            translator_class.return_value.translate.side_effect = (
                RuntimeError('service unavailable'))
            with self.assertRaises(RuntimeError):
                provider.translate_batch(['Source text'], 'en', 'es')

    def test_translate_html_sends_text_nodes_without_markup(self):
        provider = GoogletransProvider({
            'retries': 1,
            'sleep_between_calls_ms': 0,
            'timeout': 1,
        })
        with patch(
                'odoo.addons.ir_translation_auto_translation.models.'
                'googletrans_provider.GoogleTranslator') as translator_class:
            translator_class.return_value.translate.side_effect = (
                lambda value: f'Translated: {value}'
            )
            result = provider.translate(
                '<p>Es necesario traducir ésto.</p>', 'es', 'en', html=True)
            self.assertEqual(
                result, '<p>Translated: Es necesario traducir ésto.</p>')
            translator_class.return_value.translate.assert_called_once_with(
                'Es necesario traducir ésto.')


class TestDeepLProvider(BaseTranslationTest):

    def test_translate_sends_html_tag_handling(self):
        provider = DeepLProvider({
            'deepl_api_key': 'test-key:fx',
            'retries': 1,
            'sleep_between_calls_ms': 0,
        })
        response = type('Response', (), {
            'raise_for_status': lambda self: None,
            'json': lambda self: {
                'translations': [{'text': '<p>Translated</p>'}],
            },
        })()
        with patch(
                'odoo.addons.ir_translation_auto_translation.models.'
                'deepl_provider.requests.post', return_value=response) as post:
            result = provider.translate(
                '<p>Texto</p>', 'es_ES', 'en_US', html=True)
            self.assertEqual(result, '<p>Translated</p>')
            payload = post.call_args.kwargs['json']
            self.assertEqual(payload['source_lang'], 'ES')
            self.assertEqual(payload['target_lang'], 'EN-US')
            self.assertEqual(payload['tag_handling'], 'html')
            self.assertEqual(payload['tag_handling_version'], 'v2')


class TestTranslationWizard(BaseTranslationTest):
    def setUp(self):
        super().setUp()
        self.wizard = self.env['ir.translation.wizard']
        self.product = self._create_product('Wizard Test Product')

    def test_get_languages(self):
        languages = self.wizard._get_languages()
        self.assertIsInstance(languages, list)
        codes = [lang[0] for lang in languages]
        self.assertIn(self.SRC_LANG, codes)

    def test_default_source_language(self):
        default_lang = self.wizard._get_default_source_lang()
        self.assertIsInstance(default_lang, str)

    def test_action_translate_no_fields(self):
        lang_es = self._get_language(self.DEST_LANG)
        wizard = self.wizard.new({
            'model_name': self.MODEL,
            'record_id': self.product.id,
            'source_lang': self.SRC_LANG,
            'field_ids': [],
            'language_ids': [(6, 0, [lang_es.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_translate()

    def test_action_translate_no_languages(self):
        field = self._get_model_field(self.MODEL, self.FIELD)
        wizard = self.wizard.new({
            'model_name': self.MODEL,
            'record_id': self.product.id,
            'source_lang': self.SRC_LANG,
            'field_ids': [(6, 0, [field.id])],
            'language_ids': [],
        })
        with self.assertRaises(UserError):
            wizard.action_translate()

    def test_action_translate_record_not_found(self):
        field = self._get_model_field(self.MODEL, self.FIELD)
        lang = self._get_language(self.DEST_LANG)
        wizard = self.wizard.new({
            'model_name': self.MODEL,
            'record_id': 999999,
            'source_lang': self.SRC_LANG,
            'field_ids': [(6, 0, [field.id])],
            'language_ids': [(6, 0, [lang.id])],
        })
        with self.assertRaises(UserError):
            wizard.action_translate()

    def test_onchange_model_name(self):
        wizard = self.wizard.new({
            'model_name': self.MODEL,
            'record_id': self.product.id,
            'source_lang': self.SRC_LANG,
        })
        wizard.model_name = 'product.product'
        wizard._onchange_model_name()
        self.assertFalse(wizard.field_ids)


class TestBulkStatusLogFormat(BaseTranslationTest):

    def test_format_bulk_status_log_uses_one_message_per_line(self):
        wizard = self.env['ir.translation.bulk.wizard'].with_context(
            lang='en_US')
        summary = {
            'successful': 8,
            'skipped': 0,
            'errors': 9,
        }
        error_details = [
            '1179.description: Source text empty for description',
            '1179.description_picking: Source text empty for '
            'description_picking',
            '1179.website_name: El campo website_name no está almacenado, '
            'omitiendo',
        ]
        status_log = wizard._format_bulk_status_log(
            1, 17, 1, [('English (US)', summary)], error_details)
        expected_lines = [
            'Bulk Translation Complete',
            'Total Records: 1',
            'Total Fields: 17',
            'Total Languages: 1',
            'Results:',
            'English (US):',
            'Success: 8',
            'Skipped: 0',
            'Errors: 9',
            '',
            'Errors:',
            '1179.description: Source text empty for description',
            '1179.description_picking: Source text empty for '
            'description_picking',
            '1179.website_name: El campo website_name no está almacenado, '
            'omitiendo',
        ]
        self.assertEqual(status_log.split('\n'), expected_lines)
        self.assertNotIn('Success: 8, Skipped: 0', status_log)


class TestTranslationBulkWizard(BaseTranslationTest):
    def setUp(self):
        super().setUp()
        self.bulk = self.env['ir.translation.bulk.wizard']
        self.products = self._create_products(3)

    def test_get_models(self):
        models = self.bulk._get_models()
        self.assertIsInstance(models, list)
        codes = [m[0] for m in models]
        self.assertIn(self.MODEL, codes)
        self.assertIn('product.product', codes)
        self.assertIn('product.public.category', codes)

    def test_get_languages(self):
        languages = self.bulk._get_languages()
        self.assertIsInstance(languages, list)
        codes = [lang[0] for lang in languages]
        self.assertIn(self.SRC_LANG, codes)

    def test_action_no_fields(self):
        lang = self._get_language(self.DEST_LANG)
        wizard = self.bulk.new({
            'model_name': self.MODEL,
            'source_lang': self.SRC_LANG,
            'field_ids': [],
            'language_ids': [(6, 0, [lang.id])],
            'filter_type': 'all',
            'domain': '[]',
        })
        with self.assertRaises(UserError):
            wizard.action_translate_bulk()

    def test_action_no_languages(self):
        field = self._get_model_field(self.MODEL, self.FIELD)
        wizard = self.bulk.new({
            'model_name': self.MODEL,
            'source_lang': self.SRC_LANG,
            'field_ids': [(6, 0, [field.id])],
            'language_ids': [],
            'filter_type': 'all',
            'domain': '[]',
        })
        with self.assertRaises(UserError):
            wizard.action_translate_bulk()

    def test_action_no_records(self):
        field = self._get_model_field(self.MODEL, self.FIELD)
        lang = self._get_language(self.DEST_LANG)
        wizard = self.bulk.new({
            'model_name': self.MODEL,
            'source_lang': self.SRC_LANG,
            'field_ids': [(6, 0, [field.id])],
            'language_ids': [(6, 0, [lang.id])],
            'filter_type': 'domain',
            'domain': '[("name", "=", "NonExistent")]',
        })
        with self.assertRaises(UserError):
            wizard.action_translate_bulk()

    def test_invalid_domain(self):
        field = self._get_model_field(self.MODEL, self.FIELD)
        lang = self._get_language(self.DEST_LANG)
        wizard = self.bulk.new({
            'model_name': self.MODEL,
            'source_lang': self.SRC_LANG,
            'field_ids': [(6, 0, [field.id])],
            'language_ids': [(6, 0, [lang.id])],
            'filter_type': 'domain',
            'domain': '[("invalid_syntax"',
        })
        with self.assertRaises(UserError):
            wizard.action_translate_bulk()

    def test_invalid_selected_records(self):
        field = self._get_model_field(self.MODEL, self.FIELD)
        lang = self._get_language(self.DEST_LANG)
        wizard = self.bulk.new({
            'model_name': self.MODEL,
            'source_lang': self.SRC_LANG,
            'field_ids': [(6, 0, [field.id])],
            'language_ids': [(6, 0, [lang.id])],
            'filter_type': 'selected',
            'selected_record_ids': 'not_a_number',
        })
        with self.assertRaises(UserError):
            wizard.action_translate_bulk()

    def test_onchange_model_name(self):
        wizard = self.bulk.new({
            'model_name': self.MODEL,
            'source_lang': self.SRC_LANG,
            'field_ids': [],
            'language_ids': [],
            'filter_type': 'all',
        })
        wizard.model_name = 'product.product'
        wizard._onchange_model_name()
        self.assertFalse(wizard.field_ids)

    def test_company_filter_defaults_to_current_company(self):
        defaults = self.bulk.with_context(
            default_model_name=self.MODEL,
        ).default_get([
            'model_name', 'company_id', 'model_has_company'])
        self.assertEqual(defaults['company_id'], self.env.company.id)
        self.assertTrue(defaults['model_has_company'])
        wizard = self.bulk.new(defaults)
        self.assertEqual(
            wizard._get_company_domain(),
            [('company_id', '=', self.env.company.id)])


class TestProductTemplateActions(BaseTranslationTest):
    def setUp(self):
        super().setUp()
        self.product = self._create_product('Actions Test')

    def test_action_open_translation_wizard(self):
        action = self.product.action_open_translation_wizard()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'ir.translation.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(
            action['context']['default_model_name'], self.MODEL)
        self.assertEqual(
            action['context']['default_record_id'], self.product.id)

    def test_action_open_bulk_translation_wizard(self):
        action = self.product.action_open_bulk_translation_wizard()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'ir.translation.bulk.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertIn(self.product.id, action['context']['active_ids'])


class TestProductCategoryActions(BaseTranslationTest):

    def test_product_category_has_translation_action(self):
        category = self.env['product.category'].create({
            'name': 'Translation Test Category',
        })
        action = category.action_open_translation_wizard()
        self.assertEqual(action['res_model'], 'ir.translation.wizard')
        self.assertEqual(
            action['context']['default_model_name'], 'product.category')

    def test_product_public_category_has_translation_action(self):
        category = self.env['product.public.category'].create({
            'name': 'Translation Test Public Category',
        })
        action = category.action_open_translation_wizard()
        self.assertEqual(action['res_model'], 'ir.translation.wizard')
        self.assertEqual(
            action['context']['default_model_name'], 'product.public.category')

    def test_multiple_product_categories_open_bulk_translation(self):
        categories = self.env['product.category'].create([
            {'name': 'Translation Test Category 1'},
            {'name': 'Translation Test Category 2'},
        ])
        action = categories.action_open_translation_wizard()
        self.assertEqual(action['res_model'], 'ir.translation.bulk.wizard')
        self.assertEqual(
            action['context']['default_model_name'], 'product.category')
        self.assertEqual(action['context']['active_ids'], categories.ids)

    def test_category_list_translation_actions(self):
        for xml_id, model_name in (
                ('action_product_category_translation_server',
                 'product.category'),
                ('action_product_public_category_translation_server',
                 'product.public.category')):
            action = self.env.ref('ir_translation_auto_translation.%s' % xml_id)
            self.assertEqual(action.binding_model_id.model, model_name)
            self.assertEqual(action.binding_view_types, 'list')


class TestWebsitePageActions(BaseTranslationTest):

    def test_website_page_bulk_translate_server_action(self):
        action = self.env.ref(
            'ir_translation_auto_translation.'
            'action_website_page_bulk_translate_server')
        self.assertEqual(action.binding_model_id.model, 'website.page')
        self.assertEqual(action.binding_type, 'action')
        self.assertEqual(action.binding_view_types, 'list')


class TestBlogPostActions(BaseTranslationTest):

    def test_blog_post_bulk_translate_server_action(self):
        action = self.env.ref(
            'ir_translation_auto_translation.'
            'action_blog_post_bulk_translate_server')
        self.assertEqual(action.binding_model_id.model, 'blog.post')
        self.assertEqual(action.binding_type, 'action')
        self.assertEqual(action.binding_view_types, 'list')
