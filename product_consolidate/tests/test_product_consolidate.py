###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductConsolidate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.template = self.env['product.template'].create({
            'name': 'Consolidated product test',
        })

    def test_default_and_toggle_template(self):
        self.assertFalse(self.template.is_consolidated)
        self.assertTrue(self.template.toogle_consolidate_products())
        self.assertTrue(self.template.is_consolidated)
        self.template.toogle_consolidate_products()
        self.assertFalse(self.template.is_consolidated)

    def test_toggle_multiple_templates(self):
        other_template = self.env['product.template'].create({
            'name': 'Other consolidated product test',
            'is_consolidated': True,
        })
        (self.template | other_template).toogle_consolidate_products()
        self.assertTrue(self.template.is_consolidated)
        self.assertFalse(other_template.is_consolidated)

    def test_toggle_product_variant(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Consolidation attribute test',
        })
        values = self.env['product.attribute.value'].create([
            {
                'name': 'First consolidation value',
                'attribute_id': attribute.id,
            },
            {
                'name': 'Second consolidation value',
                'attribute_id': attribute.id,
            },
        ])
        self.template.attribute_line_ids = [(0, 0, {
            'attribute_id': attribute.id,
            'value_ids': [(6, 0, values.ids)],
        })]
        self.assertEqual(len(self.template.product_variant_ids), 2)
        variant = self.template.product_variant_ids[0]
        self.assertTrue(variant.toogle_consolidate_products())
        self.assertTrue(self.template.is_consolidated)
        statuses = self.template.product_variant_ids.mapped(
            'is_consolidated')
        self.assertTrue(all(statuses))

    def test_copy_resets_consolidation(self):
        self.template.is_consolidated = True
        copied_template = self.template.copy()
        self.assertFalse(copied_template.is_consolidated)

    def test_product_views_include_consolidation_button(self):
        expected_group = (
            'product_consolidate.group_product_consolidation_manager')
        view_xmlids = [
            'product.product_template_only_form_view',
            'product.product_normal_form_view',
        ]
        for xmlid in view_xmlids:
            view = self.env.ref(xmlid)
            arch = view._get_combined_arch()
            buttons = arch.xpath(
                '//button[@name="toogle_consolidate_products"]')
            self.assertEqual(len(buttons), 1)
            self.assertEqual(buttons[0].get('groups'), expected_group)
