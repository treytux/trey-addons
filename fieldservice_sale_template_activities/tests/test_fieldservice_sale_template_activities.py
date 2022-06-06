###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestFieldserviceSaleTemplateActivities(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
        })
        self.fsm_template = self.env['fsm.template'].create({
            'name': 'Test template',
            'temp_activity_ids': [
                (0, 0, {
                    'name': 'Activity 1',
                    'required': True}),
                (0, 0, {
                    'name': 'Activity 2',
                    'required': False}),
            ],
        })
        self.fsm_template2 = self.env['fsm.template'].create({
            'name': 'Test template 2',
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'FSM product test',
            'standard_price': 10,
            'list_price': 100,
            'field_service_tracking': 'sale',
            'fsm_order_template_id': self.fsm_template.id,
        })
        self.product2 = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'product test',
            'standard_price': 10,
            'list_price': 100,
            'field_service_tracking': 'sale',
            'fsm_order_template_id': self.fsm_template2.id,
        })
        self.fsm_location = self.env['fsm.location'].create({
            'name': 'Test location',
            'owner_id': self.partner.id,
        })
        self.fsm_location2 = self.env['fsm.location'].create({
            'name': 'Test location',
            'owner_id': self.partner.id,
        })

    def test_create_and_confirm_sale_with_activities(self):
        fsm_orders = self.env['fsm.order'].search([
            ('location_id', '=', self.fsm_location.id)])
        self.assertEquals(len(fsm_orders), 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        fsm_orders = self.env['fsm.order'].search([
            ('location_id', '=', self.fsm_location.id)])
        self.assertTrue(fsm_orders)
        self.assertEquals(fsm_orders.template_id, self.fsm_template)
        self.assertEquals(len(fsm_orders.order_activity_ids), 2)

    def test_create_and_confirm_sale_without_activities(self):
        fsm_orders = self.env['fsm.order'].search([
            ('location_id', '=', self.fsm_location2.id)])
        self.assertEquals(len(fsm_orders), 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.fsm_location2.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product2.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        fsm_orders = self.env['fsm.order'].search([])
        ('location_id', '=', self.fsm_location2.id)
        self.assertTrue(fsm_orders)
        self.assertEquals(fsm_orders.template_id, self.fsm_template2)
        self.assertFalse(fsm_orders.order_activity_ids)
