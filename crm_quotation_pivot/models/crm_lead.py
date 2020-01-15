###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sale_amount_total_stored = fields.Monetary(
        compute='_compute_sale_amount_total_stored',
        currency_field='company_currency',
        string='Sum of Orders',
        store=True,
    )

    @api.depends('sale_amount_total')
    @api.multi
    def _compute_sale_amount_total_stored(self):
        for obj in self:
            obj.sale_amount_total_stored = obj.sale_amount_total
