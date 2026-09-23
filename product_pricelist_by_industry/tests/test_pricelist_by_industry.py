###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestPricelistByIndustry(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.industry_a = cls.env['res.partner.industry'].create({
            'name': 'Industry A',
        })
        cls.industry_b = cls.env['res.partner.industry'].create({
            'name': 'Industry B',
        })
        cls.product = cls.env.ref('product.product_product_4b')
        cls.product.write({'list_price': 100.0})
        cls.partner_ind_a = cls.env['res.partner'].create({
            'name': 'Partner Industry A',
            'industry_id': cls.industry_a.id,
        })
        cls.partner_ind_b = cls.env['res.partner'].create({
            'name': 'Partner Industry B',
            'industry_id': cls.industry_b.id,
        })
        cls.partner_no_industry = cls.env['res.partner'].create({
            'name': 'Partner No Industry',
        })
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Industry Pricelist',
            'item_ids': [
                (0, 0, {
                    'name': 'Industry A 50% off',
                    'applied_on': '2_industry',
                    'partner_industry_id': cls.industry_a.id,
                    'compute_price': 'formula',
                    'price_discount': 50,
                    'base': 'list_price',
                }),
                (0, 0, {
                    'name': 'All products',
                    'applied_on': '3_global',
                    'compute_price': 'formula',
                    'price_discount': 0,
                    'base': 'list_price',
                }),
            ],
        })
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

    def test_industry_rule_applies_for_matching_industry(self):
        pricelist = self.pricelist.with_context(
            partner=self.partner_ind_a.id)
        price = pricelist._compute_price_rule(
            products=self.product, qty=1,
            uom=self.uom_unit, date=fields.Date.today())[self.product.id][0]
        self.assertEqual(
            float_compare(price, 50.0, precision_digits=2), 0,
            msg='Expected 50.0 (50%% of 100) for industry A, got %s' % price)

    def test_industry_rule_does_not_apply_for_other_industry(self):
        pricelist = self.pricelist.with_context(
            partner=self.partner_ind_b.id)
        price = pricelist._compute_price_rule(
            products=self.product,
            qty=1,
            uom=self.uom_unit,
            date=fields.Date.today(),
        )[self.product.id][0]
        self.assertEqual(
            float_compare(price, 100.0, precision_digits=2), 0,
            msg='Expected 100.0 (no discount) for industry B, got %s' % price)

    def test_industry_rule_does_not_apply_without_partner(self):
        price = self.pricelist._compute_price_rule(
            products=self.product,
            qty=1,
            uom=self.uom_unit,
            date=fields.Date.today(),
        )[self.product.id][0]
        self.assertEqual(
            float_compare(price, 100.0, precision_digits=2), 0,
            msg='Expected 100.0 (no discount) without partner, got %s' % price)

    def test_industry_rule_does_not_apply_without_industry_partner(self):
        pricelist = self.pricelist.with_context(
            partner=self.partner_no_industry.id)
        price = pricelist._compute_price_rule(
            products=self.product,
            qty=1,
            uom=self.uom_unit,
            date=fields.Date.today(),
        )[self.product.id][0]
        self.assertEqual(
            float_compare(price, 100.0, precision_digits=2), 0,
            msg='Expected 100.0 (no discount) for partner without industry, '
                'got %s' % price
        )

    def test_pricelist_item_name_shows_industry(self):
        item = self.pricelist.item_ids.filtered(
            lambda i: i.applied_on == '2_industry')
        self.assertTrue(item, 'Industry rule item not found')
        item._compute_name_and_price()
        expected_name = 'Industry: %s' % self.industry_a.name
        self.assertEqual(
            item.name, expected_name,
            msg='Expected item name "%s", got "%s"' % (expected_name, item.name))

    def test_onchange_applied_on_clears_industry(self):
        item = self.env['product.pricelist.item'].new({
            'pricelist_id': self.pricelist.id,
            'applied_on': '3_global',
            'partner_industry_id': self.industry_a.id,
        })
        item._onchange_applied_on()
        self.assertFalse(item.partner_industry_id)
