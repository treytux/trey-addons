###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase


class TestPricelistByIndustry(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.industry = cls.env['res.partner.industry'].create({
            'name': 'Industry for pricelist',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Product',
            'type': 'consu',
            'lst_price': 100.0,
        })
        cls.customer_pricelist = cls.env['product.pricelist'].create({
            'name': 'Customer Pricelist',
            'item_ids': [(0, 0, {
                'name': 'Industry',
                'applied_on': '2_industry',
                'partner_industry_id': cls.industry.id,
                'compute_price': 'formula',
                'price_discount': 25,
                'base': 'list_price',
            }), (0, 0, {
                'name': 'All products',
                'applied_on': '3_global',
                'compute_price': 'formula',
                'price_discount': 0,
                'base': 'list_price',
            })]
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner',
            'industry_id': cls.industry.id,
            'property_product_pricelist': cls.customer_pricelist.id,
        })

    def test_calculation_price_of_products_by_industry(self):
        context = {
            'pricelist': self.customer_pricelist.id,
            'partner': self.partner,
            'quantity': 1,
        }
        self.product = self.product.with_context(context)
        self.assertEqual(self.product.price, 75.0)
        self.partner.industry_id = False
        self.product.refresh()
        self.assertEqual(self.product.price, 100.0)
        self.partner.industry_id = self.industry.id
        context = {
            'pricelist': self.customer_pricelist.id,
            'partner_id': self.partner.id,
            'quantity': 1,
        }
        self.product = self.product.with_context(context)
        self.assertEqual(self.product.price, 75.0)
        self.partner.industry_id = False
        self.product.refresh()
        self.assertEqual(self.product.price, 100.0)
