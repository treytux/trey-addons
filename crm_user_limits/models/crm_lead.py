###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.depends('order_ids', 'order_ids.state')
    def _compute_sale_amount_total(self):
        def get_sale_total(sale):
            company_currency = self.env.user.company_id.currency_id
            return sale.currency_id._convert(
                sale.amount_untaxed,
                lead.company_currency or company_currency,
                sale.company_id,
                sale.date_order or fields.Date.today())

        super()._compute_sale_amount_total()
        states = ['pending-approve', 'draft', 'sent']
        for lead in self:
            sales = lead.order_ids.filtered(
                lambda s: s.state not in states + ['cancel'])
            lead.sale_amount_total = sum([get_sale_total(s) for s in sales])
            lead.sale_number = len(lead.order_ids.filtered(
                lambda s: s.state in states))
