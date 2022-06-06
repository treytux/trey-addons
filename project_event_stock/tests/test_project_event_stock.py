###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectEventStock(TransactionCase):

    def test_project_product(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
        })
        status = self.env['project.status'].create({
            'name': 'Generate events',
            'not_modify_event': True,
        })
        project = self.env['project.project'].create({
            'name': 'Project test',
            'event_line_ids': [
                (0, 0, {
                    'address_id': partner.id,
                    'date_begin': '2022/01/01 12:30:00',
                    'date_end': '2022/01/01 13:30:00',
                    'repeat': 5,
                    'period': 'day',
                }),
            ],
            'product_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'quantity': 10,
                }),
            ],
        })
        project.project_status = status.id
        self.assertEquals(len(project.event_ids), 5)
        event = project.event_ids[0]
        self.assertEquals(len(event.product_ids), 1)
        event.button_confirm()
        self.assertEquals(
            sum(event.product_ids.mapped('stock_move_ids.product_uom_qty')),
            10)
