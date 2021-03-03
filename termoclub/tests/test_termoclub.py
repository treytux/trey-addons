###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestTermoClub(TransactionCase):

    def setUp(self):
        super().setUp()
        self.termoclub_supplier = self.env.ref(
            'termoclub.res_partner_termoclub')
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
            'customer': True,
            'supplier': False,
        })
        self.company = self.env.user.company_id
        self.company.write({
            'termoclub_supplier_id': self.termoclub_supplier.id,
            'termoclub_wsdl': self.env.user.company_id.termoclub_wsdl,
            'termoclub_user': 'NEDCONFO',
            'termoclub_password': 'NEDCONFO',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product', 'company_id': self.env.user.company_id.id,
            'name': 'FONDITAL CALDERA COND.ITACA KRB32N ERP KITS02KU32',
            'default_code': 'FONDITACAKRB32',
            'barcode': '4317784094610',
            'standard_price': 2.92,
            'list_price': 6.08,
            'purchase_ok': True,
            'sale_ok': True,
            'seller_ids': [(0, 0, {
                'name': self.termoclub_supplier.id,
                'product_code': 'FONDITACAKRB32'
            })],
        })

    def test_product_stock(self):
        res = self.product_01.action_termoclub_check_stock()
        self.assertEquals(res.find('ERROR'), -1)

    def test_purchase_order(self):
        self.purchase = self.env['purchase.order'].create({
            'partner_id': self.termoclub_supplier.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_01.name,
                    'product_id': self.product_01.id,
                    'product_qty': 5.0,
                    'product_uom': self.product_01.uom_po_id.id,
                    'price_unit': 500.0,
                    'date_planned': datetime.today().strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        self.assertTrue(self.purchase.order_line[0].product_id.is_termoclub)
        res = self.purchase.order_line[0].action_termoclub_check_stock()
        self.assertEquals(res.find('ERROR'), -1)
