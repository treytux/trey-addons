###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderStage(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_sale_stage(self):
        stage_1 = self.env['sale.order.stage'].create({
            'name': 'Test stage ONE',
            'sequence': 10,
        })
        stage_2 = self.env['sale.order.stage'].create({
            'name': 'Test stage TWO',
            'sequence': 20,
        })
        sale_base = self.env.ref('sale.sale_order_1')
        sale = self.env['sale.order'].create({
            'partner_id': sale_base.partner_id.id,
        })
        self.assertEqual(sale.stage_id, stage_1)
        sale.stage_id = stage_2.id
        self.assertEqual(sale.stage_id, stage_2)
        stage_1.sequence = 99
        sale_create = self.env['sale.order'].create({
            'partner_id': sale.partner_id.id,
        })
        self.assertEqual(sale_create.stage_id, stage_2)
        sale.stage_id = stage_1.id
        sale_copy = sale.copy()
        self.assertEqual(sale_copy.stage_id, stage_2)
