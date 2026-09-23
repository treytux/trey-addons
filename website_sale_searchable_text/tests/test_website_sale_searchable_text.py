###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestWebsiteSaleSearchableText(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
            'value_ids': [
                (0, 0, {'name': 'White'}),
                (0, 0, {'name': 'Black'}),
            ],
        })
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test product 1',
            'type': 'consu',
            'default_code': 'T0001',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })

    def test_compute_searchable_text(self):
        variants = self.product_tmpl.product_variant_ids
        self.assertEqual(len(variants), 2)
        self.assertIn('Test product 1', self.product_tmpl.searchable_text)
        self.product_tmpl.name = 'Test 1'
        self.assertIn('Test 1', self.product_tmpl.searchable_text)
        self.product_tmpl.website_description = '<p>Cordless drill</p>'
        self.product_tmpl.hidden_mapping = 'rare synonym'
        self.assertIn('Cordless drill', self.product_tmpl.searchable_text)
        self.assertIn('rare synonym', self.product_tmpl.searchable_text)
        variants[0].default_code = 'CODE1'
        variants[1].default_code = 'CODE2'
        self.assertIn('CODE1', self.product_tmpl.searchable_text)
        self.assertIn('CODE2', self.product_tmpl.searchable_text)

    def _search_detail(self):
        website = self.env['website'].get_current_website()
        return self.env['product.template']._search_get_detail(
            website, 'name asc', {
                'displayImage': False,
                'displayDescription': False,
                'displayExtraLink': False,
                'displayDetail': False,
            })

    def test_search_detail_registers_field(self):
        detail = self._search_detail()
        self.assertIn('searchable_text', detail['search_fields'])

    def test_shop_search_matches_hidden_mapping(self):
        self.product_tmpl.write({
            'is_published': True,
            'hidden_mapping': 'zzytoken',
        })
        detail = self._search_detail()
        results, _count = self.env['product.template']._search_fetch(
            detail, 'zzytoken', 10, 'name asc')
        self.assertIn(self.product_tmpl, results)
