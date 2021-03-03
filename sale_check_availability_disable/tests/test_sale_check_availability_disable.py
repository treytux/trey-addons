###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleCheckAvailabilityDisable(TransactionCase):

    def test_simulator_wizard(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 100,
            'list_price': 125,
        })
        group = self.env.ref(
            'sale_check_availability_disable.show_availability_sale_warning')
        group.users = [(4, self.env.user.id)]
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        line = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'product_id': product.id,
            'price_unit': 125,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
        })
        res = line._onchange_product_id_check_availability()
        self.assertNotEquals(res, {})
        group.users = [(2, self.env.user.id)]
        res = line._onchange_product_id_check_availability()
        self.assertEquals(res, {})
