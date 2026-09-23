###############################################################################
# For copyright and license notices, see __manifest__.py file
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderTypeFromProject(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        wh = self.env['stock.warehouse'].search([], limit=1)
        self.order_type = self.env['sale.order.type'].create({
            'name': 'Test order type',
            'warehouse_id': wh[0].id,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test project',
            'sale_order_type_id': self.order_type.id,
            'partner_id': self.partner.id,
        })

    def test_sale_order_type_from_project(self):
        wh = self.env['stock.warehouse'].search([])[0]
        order = self.env['sale.order'].create({
            'project_id': self.project.id,
            'warehouse_id': wh.id,
            'picking_policy': 'direct',
            'partner_id': self.partner.id,
        })
        order._onchange_project_sale_order_type()
        self.assertEqual(order.type_id.id, self.order_type.id)

    def test_sale_order_type_cleared_without_project_type(self):
        project = self.env['project.project'].create({
            'name': 'Project without sale order type',
            'partner_id': self.partner.id,
        })
        order = self.env['sale.order'].create({
            'project_id': project.id,
            'partner_id': self.partner.id,
            'type_id': self.order_type.id,
        })
        order._onchange_project_sale_order_type()
        self.assertFalse(order.type_id)
