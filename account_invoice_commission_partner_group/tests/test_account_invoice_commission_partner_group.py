###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoiceCommissionPartnerGroup(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.partner_invoice_id = self.env['res.partner'].create({
            'name': 'Test partner invoice',
            'is_company': True,
        })
        self.partner_group = self.env['res.partner'].create({
            'name': 'Test partner group 1',
            'is_company': False,
        })
        self.commission_10 = self.env['sale.commission'].create({
            'name': 'Commission test 10%',
            'fix_qty': 10,
        })
        self.commission_20 = self.env['sale.commission'].create({
            'name': 'Commission test 20%',
            'fix_qty': 20,
        })
        self.agent_01 = self.env['res.partner'].create({
            'name': 'Agent test 1',
            'agent': True,
            'agent_type': 'agent',
            'email': 'agent1@agent.com',
            'commission': self.commission_10.id,
            'settlement': 'monthly',
        })
        self.agent_02 = self.env['res.partner'].create({
            'name': 'Agent test 2',
            'agent': True,
            'agent_type': 'agent',
            'email': 'agent2@agent.com',
            'commission': self.commission_20.id,
            'settlement': 'monthly',
        })
        self.partner.write({
            'agents': [(6, 0, [self.agent_01.id])]
        })
        self.partner_invoice_id.write({
            'agents': [(6, 0, [self.agent_02.id])]
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 40,
        })

    def create_sale(self, partner):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.onchange_partner_id()
        return sale

    def test_compute_invoice_commissions_01(self):
        self.assertFalse(self.partner.partner_group_id)
        sale = self.create_sale(self.partner)
        self.assertFalse(sale.partner_group_id)
        self.assertEqual(sale.partner_id, sale.partner_invoice_id)
        self.assertEqual(sale.commission_total, 1)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.partner_id, sale.partner_id)
        self.assertEqual(invoice.partner_id, sale.partner_invoice_id)
        self.assertEqual(invoice.commission_total, 1)
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_01 = agent_sale_line.agent
        amount_sale_line_01 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_01, sale.commission_total)
        self.assertIn(agent_sale_line_01.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_01 = agent_invoice_line.agent
        amount_invoice_line_01 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_01.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_01, invoice.commission_total)
        sale.recompute_lines_agents()
        invoice.recompute_lines_agents()
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_02 = agent_sale_line.agent
        amount_sale_line_02 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_02, sale.commission_total)
        self.assertIn(agent_sale_line_02.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_02 = agent_invoice_line.agent
        amount_invoice_line_02 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_02.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_02, invoice.commission_total)

    def test_compute_invoice_commissions_02(self):
        self.assertFalse(self.partner.partner_group_id)
        self.partner.partner_group_id = self.partner_group.id
        self.assertTrue(self.partner.partner_group_id)
        sale = self.create_sale(self.partner)
        self.assertTrue(sale.partner_group_id)
        self.assertEqual(sale.partner_id, sale.partner_invoice_id)
        self.assertEqual(sale.commission_total, 1)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.partner_id, sale.partner_id)
        self.assertEqual(invoice.partner_id, sale.partner_invoice_id)
        self.assertEqual(invoice.commission_total, 1)
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_01 = agent_sale_line.agent
        amount_sale_line_01 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_01, sale.commission_total)
        self.assertIn(agent_sale_line_01.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_01 = agent_invoice_line.agent
        amount_invoice_line_01 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_01.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_01, invoice.commission_total)
        sale.recompute_lines_agents()
        invoice.recompute_lines_agents()
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_02 = agent_sale_line.agent
        amount_sale_line_02 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_02, sale.commission_total)
        self.assertIn(agent_sale_line_02.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_02 = agent_invoice_line.agent
        amount_invoice_line_02 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_02.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_02, invoice.commission_total)

    def test_compute_invoice_commissions_03(self):
        self.assertFalse(self.partner.partner_group_id)
        self.partner.partner_group_id = self.partner_group.id
        self.assertTrue(self.partner.partner_group_id)
        sale = self.create_sale(self.partner)
        self.assertEqual(sale.partner_id, self.partner)
        self.assertTrue(sale.partner_group_id)
        self.assertEqual(sale.partner_invoice_id, sale.partner_id)
        sale.partner_invoice_id = self.partner_invoice_id.id
        self.assertNotEqual(sale.partner_invoice_id, sale.partner_id)
        self.assertEqual(sale.partner_invoice_id, self.partner_invoice_id)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.partner_id, sale.partner_invoice_id)
        self.assertEqual(invoice.partner_id, self.partner_invoice_id)
        self.assertNotEqual(invoice.partner_id, self.partner)
        self.assertNotEqual(invoice.partner_id, sale.partner_id)
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_01 = agent_sale_line.agent
        amount_sale_line_01 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_01, sale.commission_total)
        self.assertIn(agent_sale_line_01.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_01 = agent_invoice_line.agent
        amount_invoice_line_01 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_01.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_01, invoice.commission_total)
        sale.recompute_lines_agents()
        invoice.recompute_lines_agents()
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_02 = agent_sale_line.agent
        amount_sale_line_02 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_02, sale.commission_total)
        self.assertIn(agent_sale_line_02.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_02 = agent_invoice_line.agent
        amount_invoice_line_02 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_02.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_02, invoice.commission_total)

    def test_compute_invoice_commissions_04(self):
        self.assertFalse(self.partner.partner_group_id)
        sale = self.create_sale(self.partner)
        self.assertEqual(sale.partner_id, self.partner)
        self.assertFalse(sale.partner_group_id)
        self.assertEqual(sale.partner_invoice_id, sale.partner_id)
        sale.partner_invoice_id = self.partner_invoice_id.id
        self.assertNotEqual(sale.partner_invoice_id, sale.partner_id)
        self.assertEqual(sale.partner_invoice_id, self.partner_invoice_id)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.partner_id, sale.partner_invoice_id)
        self.assertEqual(invoice.partner_id, self.partner_invoice_id)
        self.assertNotEqual(invoice.partner_id, self.partner)
        self.assertNotEqual(invoice.partner_id, sale.partner_id)
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_01 = agent_sale_line.agent
        amount_sale_line_01 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_01, sale.commission_total)
        self.assertIn(agent_sale_line_01.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_01 = agent_invoice_line.agent
        amount_invoice_line_01 = agent_invoice_line.amount
        self.assertIn(agent_invoice_line_01.id, sale.partner_id.agents.ids)
        self.assertEqual(amount_invoice_line_01, invoice.commission_total)
        sale.recompute_lines_agents()
        invoice.recompute_lines_agents()
        agent_sale_line = self.env['sale.order.line.agent'].search([
            ('object_id', '=', sale.order_line[0].id),
        ])
        agent_sale_line_02 = agent_sale_line.agent
        amount_sale_line_02 = agent_sale_line.amount
        self.assertEqual(amount_sale_line_02, sale.commission_total)
        self.assertIn(agent_sale_line_02.id, sale.partner_id.agents.ids)
        agent_invoice_line = self.env['account.invoice.line.agent'].search([
            ('object_id', '=', invoice.invoice_line_ids[0].id),
        ])
        agent_invoice_line_02 = agent_invoice_line.agent
        amount_invoice_line_02 = agent_invoice_line.amount
        self.assertNotIn(agent_invoice_line_02.id, sale.partner_id.agents.ids)
        self.assertIn(
            agent_invoice_line_02.id, sale.partner_invoice_id.agents.ids)
        self.assertEqual(amount_invoice_line_02, invoice.commission_total)
