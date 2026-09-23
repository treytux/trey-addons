###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import zipfile

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from PIL import Image


class TestProductImageImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Importable product',
            'default_code': '31GTIAS',
            'company_id': self.env.company.id,
        })

    def _image(self, color):
        stream = io.BytesIO()
        Image.new('RGB', (10, 10), color=color).save(stream, 'JPEG')
        return stream.getvalue()

    def _zip(self, files):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return base64.b64encode(stream.getvalue())

    def _wizard(self, files):
        return self.env['website.sale.product.image.import'].create({
            'zip_file': self._zip(files),
            'filename': 'images.zip',
        })

    def test_variant_destination_stores_images_on_variant(self):
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
        })
        wizard.image_destination = 'variant'
        wizard.action_import()
        self.assertTrue(self.product.image_variant_1920)
        self.assertFalse(self.product.product_tmpl_id.image_1920)

    def test_import_main_and_extra_images_in_order(self):
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
            '31GTIAS-2.jpg': self._image('green'),
            '31GTIAS-3.jpg': self._image('blue'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 3)
        template_images = (
            self.product.product_tmpl_id.product_template_image_ids)
        self.assertEqual(len(template_images), 2)
        self.assertEqual(template_images.mapped('sequence'), [10, 20])
        self.assertTrue(self.product.product_tmpl_id.image_1920)
        self.assertFalse(wizard.not_found_references)
        self.assertFalse(wizard.invalid_files)

    def test_validation_does_not_modify_product_images(self):
        original_image = base64.b64encode(self._image('black'))
        self.product.write({'image_variant_1920': original_image})
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
            '31GTIAS-2.jpg': self._image('green'),
        })
        result = wizard.action_validate()
        self.assertEqual(wizard.state, 'validated')
        self.assertEqual(wizard.loaded_count, 2)
        self.assertIn('Products validated: 1', wizard.summary)
        self.assertIn('Images validated: 2', wizard.summary)
        self.assertEqual(self.product.image_variant_1920, original_image)
        self.assertEqual(result['context'], {
            'import_done': False,
            'validation_done': True,
        })

    def test_import_replaces_existing_images(self):
        self.product.write({
            'image_variant_1920': base64.b64encode(self._image('black')),
            'product_variant_image_ids': [
                (0, 0, {
                    'name': 'old',
                    'image_1920': base64.b64encode(self._image('white')),
                }),
            ],
        })
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
        })
        wizard.action_import()
        self.assertFalse(
            self.product.product_tmpl_id.product_template_image_ids)
        self.assertEqual(wizard.loaded_count, 1)

    def test_report_contains_not_found_and_invalid_files(self):
        wizard = self._wizard({
            'UNKNOWN-1.jpg': self._image('red'),
            'bad-name.jpg': self._image('green'),
        })
        wizard.action_import()
        self.assertIn('UNKNOWN', wizard.not_found_references)
        self.assertIn('bad-name.jpg', wizard.invalid_files)

    def test_missing_one_or_number_one_is_not_loaded(self):
        wizard = self._wizard({
            '31GTIAS-2.jpg': self._image('red'),
            '31GTIAS-4.jpg': self._image('green'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 0)
        self.assertIn('31GTIAS', wizard.invalid_files)

    def test_extreme_image_number_is_rejected_without_memory_allocation(self):
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
            '31GTIAS-%s.jpg' % (10 ** 30): self._image('green'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 0)
        self.assertIn('Image numbering must be consecutive.',
                      wizard.invalid_files)

    def test_invalid_image_is_reported(self):
        wizard = self._wizard({
            '31GTIAS-1.jpg': b'not an image',
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 0)
        self.assertIn('31GTIAS-1.jpg', wizard.invalid_files)

    def test_unsupported_extension_is_reported(self):
        wizard = self._wizard({
            '31GTIAS-1.gif': self._image('red'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 0)
        self.assertIn('31GTIAS-1.gif', wizard.invalid_files)

    def test_duplicate_number_is_reported_without_replacing_images(self):
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
            '31GTIAS-1.png': self._image('green'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 0)
        self.assertIn('31GTIAS', wizard.invalid_files)

    def test_valid_product_is_loaded_after_another_product_error(self):
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
            'UNKNOWN-1.jpg': self._image('green'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 1)
        self.assertIn('UNKNOWN', wizard.not_found_references)

    def test_product_from_another_company_is_not_loaded(self):
        other_company = self.env['res.company'].create({
            'name': 'Other test company',
        })
        other_product = self.env['product.product'].create({
            'name': 'Other company product',
            'default_code': 'OTHER-COMPANY',
            'company_id': other_company.id,
        })
        wizard = self._wizard({
            'OTHER-COMPANY-1.jpg': self._image('red'),
        })
        wizard.action_import()
        self.assertFalse(other_product.image_variant_1920)
        self.assertIn('OTHER-COMPANY', wizard.not_found_references)

    def test_archived_product_does_not_make_reference_ambiguous(self):
        archived_product = self.env['product.product'].create({
            'name': 'Archived product',
            'default_code': '31GTIAS',
            'company_id': self.env.company.id,
            'active': False,
        })
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
        })
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 1)
        self.assertFalse(archived_product.image_variant_1920)

    def test_archived_product_is_excluded_even_with_inactive_context(self):
        archived_product = self.env['product.product'].create({
            'name': 'Archived product',
            'default_code': 'ARCHIVED-CONTEXT',
            'company_id': self.env.company.id,
            'active': False,
        })
        wizard = self._wizard({
            'ARCHIVED-CONTEXT-1.jpg': self._image('red'),
        }).with_context(active_test=False)
        wizard.action_import()
        self.assertEqual(wizard.loaded_count, 0)
        self.assertFalse(archived_product.image_variant_1920)
        self.assertIn('ARCHIVED-CONTEXT', wizard.not_found_references)

    def test_corrupt_zip_raises_user_error(self):
        wizard = self.env['website.sale.product.image.import'].create({
            'zip_file': base64.b64encode(b'not a zip'),
            'filename': 'images.zip',
        })
        with self.assertRaisesRegex(
                UserError, 'The selected file is not a valid ZIP archive.'):
            wizard.action_import()

    def _template_with_variants(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Import color',
            'value_ids': [(0, 0, {'name': name}) for name in ['Red', 'Blue']],
        })
        template = self.env['product.template'].create({
            'name': 'Import shirt',
            'company_id': self.env.company.id,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(6, 0, attribute.value_ids.ids)],
            })],
        })
        for variant, reference in zip(
                template.product_variant_ids, ['SHIRT-A', 'SHIRT-B']):
            variant.write({
                'default_code': reference,
                'image_variant_1920': base64.b64encode(self._image('black')),
                'product_variant_image_ids': [(0, 0, {
                    'name': reference,
                    'image_1920': base64.b64encode(self._image('white')),
                })],
            })
        template.write({
            'image_1920': base64.b64encode(self._image('green')),
            'product_template_image_ids': [(0, 0, {
                'name': 'Original template image',
                'image_1920': base64.b64encode(self._image('blue')),
            })],
        })
        return template

    def _image_snapshot(self, template):
        variants = template.product_variant_ids
        extras = (
            template.product_template_image_ids
            | variants.mapped('product_variant_image_ids'))
        return (
            template.image_1920,
            [(variant.id, variant.image_variant_1920) for variant in variants],
            [(extra.id, extra.image_1920) for extra in extras])

    def test_template_import_preserves_variant_images(self):
        template = self._template_with_variants()
        variants = template.product_variant_ids
        old_main = template.image_1920
        old_extras = template.product_template_image_ids
        variant_main = variants.mapped('image_variant_1920')
        variant_extras = variants.mapped('product_variant_image_ids')
        extra_content = variant_extras.mapped('image_1920')
        wizard = self._wizard({
            'SHIRT-A-1.jpg': self._image('red'),
            'SHIRT-A-2.jpg': self._image('green'),
        })
        wizard.action_import()
        self.assertNotEqual(template.image_1920, old_main)
        self.assertFalse(old_extras.exists())
        self.assertEqual(len(template.product_template_image_ids), 1)
        self.assertEqual(variants.mapped('image_variant_1920'), variant_main)
        self.assertEqual(
            variants.mapped('product_variant_image_ids'), variant_extras)
        self.assertEqual(variant_extras.mapped('image_1920'), extra_content)

    def test_template_conflicts_skip_all_references_in_any_order(self):
        template = self._template_with_variants()
        original = self._image_snapshot(template)
        items = [
            ('SHIRT-A-1.jpg', self._image('red')),
            ('SHIRT-B-1.jpg', self._image('blue')),
            ('31GTIAS-1.jpg', self._image('green')),
        ]
        for files in [dict(items), dict(reversed(items))]:
            wizard = self._wizard(files)
            wizard.action_import()
            self.assertEqual(wizard.error_count, 1)
            self.assertIn('SHIRT-A, SHIRT-B', wizard.errors)
            self.assertIn(template.display_name, wizard.errors)
            self.assertIn('ID %s' % template.id, wizard.errors)
            self.assertEqual(wizard.loaded_product_count, 1)
            self.assertEqual(wizard.loaded_count, 1)
            self.assertEqual(self._image_snapshot(template), original)
        self.assertTrue(self.product.product_tmpl_id.image_1920)

    def test_invalid_reference_does_not_allow_template_overwrite(self):
        template = self._template_with_variants()
        original = self._image_snapshot(template)
        invalid_files = [
            ('SHIRT-B-1.jpg', b'not an image'),
            ('SHIRT-B-2.jpg', self._image('red')),
            ('SHIRT-B-1.gif', self._image('red')),
        ]
        for name, content in invalid_files:
            wizard = self._wizard({
                'SHIRT-A-1.jpg': self._image('red'),
                name: content,
            })
            wizard.action_import()
            self.assertEqual(wizard.error_count, 1)
            self.assertTrue(wizard.invalid_count)
            self.assertEqual(wizard.loaded_count, 0)
            self.assertEqual(wizard.loaded_product_count, 0)
            self.assertEqual(self._image_snapshot(template), original)

    def test_validation_reports_template_conflicts_without_writes(self):
        template = self._template_with_variants()
        original = self._image_snapshot(template)
        wizard = self._wizard({
            'SHIRT-A-1.jpg': self._image('red'),
            'SHIRT-B-1.jpg': self._image('blue'),
        })
        wizard.action_validate()
        self.assertEqual(wizard.state, 'validated')
        self.assertEqual(wizard.error_count, 1)
        self.assertEqual(wizard.loaded_count, 0)
        self.assertEqual(wizard.loaded_product_count, 0)
        self.assertEqual(self._image_snapshot(template), original)

    def test_import_rechecks_conflicts_after_validation(self):
        template = self._template_with_variants()
        original = self._image_snapshot(template)
        wizard = self._wizard({
            'SHIRT-A-1.jpg': self._image('red'),
            '31GTIAS-1.jpg': self._image('blue'),
        })
        wizard.action_validate()
        self.assertFalse(wizard.errors)
        self.product.default_code = 'UNRELATED'
        template.product_variant_ids[1].default_code = '31GTIAS'
        wizard.action_import()
        self.assertEqual(wizard.error_count, 1)
        self.assertEqual(wizard.loaded_count, 0)
        self.assertEqual(self._image_snapshot(template), original)

    def test_variant_import_does_not_conflict_on_shared_template(self):
        template = self._template_with_variants()
        original_main = template.image_1920
        original_extras = template.product_template_image_ids
        variants = template.product_variant_ids
        old_extras = variants.mapped('product_variant_image_ids')
        wizard = self._wizard({
            'SHIRT-A-1.jpg': self._image('red'),
            'SHIRT-A-2.jpg': self._image('green'),
            'SHIRT-B-1.jpg': self._image('blue'),
        })
        wizard.image_destination = 'variant'
        wizard.action_import()
        self.assertFalse(wizard.errors)
        self.assertEqual(wizard.loaded_product_count, 2)
        self.assertEqual(wizard.loaded_count, 3)
        self.assertFalse(old_extras.exists())
        self.assertEqual(len(variants.mapped('product_variant_image_ids')), 1)
        self.assertNotEqual(
            variants[0].image_variant_1920, variants[1].image_variant_1920)
        self.assertEqual(template.image_1920, original_main)
        self.assertEqual(template.product_template_image_ids, original_extras)

    def test_shared_reference_on_same_template_is_accepted(self):
        template = self._template_with_variants()
        template.product_variant_ids.write({
            'default_code': 'SHARED',
        })
        wizard = self._wizard({
            'SHARED-1.jpg': self._image('red'),
        })
        wizard.action_import()
        self.assertFalse(wizard.errors)
        self.assertEqual(wizard.loaded_product_count, 1)
        self.assertEqual(wizard.loaded_count, 1)

    def test_reference_on_different_templates_remains_ambiguous(self):
        template = self._template_with_variants()
        self.product.default_code = 'SHIRT-A'
        original = self._image_snapshot(template)
        wizard = self._wizard({
            'SHIRT-A-1.jpg': self._image('red'),
        })
        wizard.action_import()
        self.assertEqual(wizard.error_count, 1)
        self.assertIn('multiple product templates', wizard.errors)
        self.assertEqual(wizard.loaded_count, 0)
        self.assertEqual(self._image_snapshot(template), original)

    def test_spanish_report_distinguishes_validation_and_import(self):
        self.env['res.lang']._activate_lang('es_ES')
        wizard = self._wizard({
            '31GTIAS-1.jpg': self._image('red'),
            '31GTIAS-2.jpg': self._image('green'),
            'UNKNOWN-1.jpg': self._image('blue'),
            'MISSING-2.jpg': self._image('blue'),
        }).with_context(lang='es_ES')
        wizard.action_validate()
        self.assertIn('Productos validados: 1', wizard.summary)
        self.assertIn('Imágenes validadas: 2', wizard.summary)
        self.assertIn('2 imágenes validadas', wizard.loaded_images)
        self.assertIn('plantilla de producto ID', wizard.loaded_images)
        self.assertIn('no se ha encontrado', wizard.not_found_references)
        self.assertIn('Se requiere la imagen número 1.', wizard.invalid_files)
        wizard.action_import()
        self.assertIn('Productos cargados: 1', wizard.summary)
        self.assertIn('Imágenes cargadas: 2', wizard.summary)
        self.assertIn('2 imágenes cargadas', wizard.loaded_images)
