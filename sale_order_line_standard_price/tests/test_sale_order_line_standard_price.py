###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderLineStandardPrice(TransactionCase):

    def test_create_line(self):
        product = self.env['product.product'].create({
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 100,
            'list_price': 150,
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id
        })
        line = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'product_id': product.id,
        })
        line.product_id_change()
        line = line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.standard_price, 100)
        report = self.env['sale.report'].search(
            [('product_id', '=', product.id)])
        self.assertEquals(report.standard_price, product.standard_price)
