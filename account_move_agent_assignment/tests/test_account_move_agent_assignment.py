###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountMoveAgentAssignment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.commission_net_paid = self.env['commission'].create({
            'name': '20% fixed commission (Net amount) - Payment Based',
            'fix_qty': 20.0,
            'invoice_state': 'paid',
            'amount_base_type': 'net_amount',
        })
        self.agent = self.env['res.partner'].create({
            'name': 'Agent',
            'agent': True,
            'email': 'agent01@test.com',
            'commission_id': self.commission_net_paid.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Customer',
            'is_company': True,
            'customer_rank': 1,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test Product',
            'standard_price': 5,
            'list_price': 50,
        })

    def test_invoice_assignment_agent(self):
        journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
        })
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('type', '=', 'sale'),
        ], limit=1)
        invoice = self.env['account.move'].create({
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_01.id,
                'name': self.product_01.name,
                'price_unit': 100,
                'quantity': 1})],
        })
        invoice.action_post()
        wizard = self.env['account.move.agent.assignment'].with_context({
            'active_ids': invoice.ids,
            'active_id': invoice.id,
        }).create({
            'agents': [(6, 0, [self.agent.id])],
        })
        wizard.button_accept()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.agent_ids.agent_id.id, self.agent.id)
