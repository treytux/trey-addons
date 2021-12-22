###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerZone(TransactionCase):
    def test_partner_zone(self):
        zone_a = self.env['res.partner.zone'].create({
            'name': 'Zone A',
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'zone_id': zone_a.id,
        })
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertEquals(partner.zone_id, sale.zone_id)
