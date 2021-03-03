###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class SaleOrderAgentAssignment(TransactionCase):

    def setUp(self):
        super(SaleOrderAgentAssignment, self).setUp()
        self.commission_net_paid = self.env['sale.commission'].create({
            'name': '20% fixed commission (Net amount) - Payment Based',
            'fix_qty': 20.0,
            'invoice_state': 'paid',
            'amount_base_type': 'net_amount',
        })
        self.agent_01 = self.env['res.partner'].create({
            'name': 'Agent 01',
            'agent': True,
            'email': 'agent01@test.com',
            'commission': self.commission_net_paid.id,
        })
        self.agent_02 = self.env['res.partner'].create({
            'name': 'Agent 02',
            'agent': True,
            'email': 'agent02@test.com',
            'commission': self.commission_net_paid.id,
        })
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522',
            'agents': [(6, 0, [self.agent_01.id])],
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test Product',
            'standard_price': 5,
            'list_price': 50,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test Product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                    'agents': [(0, 0, {
                        'agent': self.agent_01.id,
                        'commission': self.commission_net_paid.id,
                    })],
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                    'agents': [(0, 0, {
                        'agent': self.agent_01.id,
                        'commission': self.commission_net_paid.id,
                    })],
                }),
            ]
        })
        for line in self.sale.order_line:
            self.assertEqual(line.agents.agent.id, self.agent_01.id)

    def test_sale_order_agent_assignment_1agent(self):
        wizard = self.env['sale.order.agent.assignment'].with_context({
            'active_ids': self.sale.ids,
            'active_id': self.sale.id,
        }).create({
            'agents': [(6, 0, [self.agent_02.id])],
        })
        wizard.button_accept()
        for line in self.sale.order_line:
            self.assertEqual(line.agents.agent.id, self.agent_02.id)
