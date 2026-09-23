###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import Form, HttpCase


class TestSaleImportSaleOrderTemplate(HttpCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 50,
            'list_price': 50,
        })

    def test_sale(self):
        self.partner.sale_note = 'This is a default sale note.'
        other_partner = self.env.ref('base.res_partner_4')
        with Form(self.env['sale.order']) as sale:
            sale.partner_id = self.partner
            self.assertEqual(sale.note, '<p>This is a default sale note.</p>')
            sale.partner_id = other_partner
            self.assertEqual(sale.note, '<p>This is a default sale note.</p>')
            sale.note = 'Changed!'
            sale.partner_id = self.partner
            self.assertEqual(sale.note, 'Changed!')
            sale.partner_id = other_partner
            sale.note = '<div>   </div><p>   </p><br>   <span>   </span>'
            sale.partner_id = self.partner
            self.assertEqual(sale.note, '<p>This is a default sale note.</p>')
