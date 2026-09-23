###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    partner_group_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner group',
    )

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        partner = self.partner_id.commercial_partner_id
        self.partner_group_id = partner.partner_group_id
        return res
