###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestCrmUserLimits(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'email': 'user@test.com',
            'company_id': self.env.user.company_id.id,
        })

    def test_crm_limits(self):
        lead = self.env['crm.lead'].sudo(self.user).create({
            'name': 'Lead test',
            'partner_id': self.partner.id,
        })
        sale_obj = self.env['sale.order'].sudo(self.user)
        auto_done = self.env['ir.config_parameter'].sudo().get_param(
            'sale.auto_done_setting')
        self.assertEquals(auto_done, False)
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'opportunity_id': lead.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1})]
        })
        self.assertEquals(lead.sale_number, 1)
        self.assertEquals(lead.sale_amount_total, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        self.assertEquals(lead.sale_number, 1)
        self.assertEquals(lead.sale_amount_total, 0)
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 1000
        sale.action_approve()
        self.assertEquals(sale.state, 'draft')
        self.assertEquals(lead.sale_amount_total, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(lead.sale_amount_total, sale.amount_untaxed)
