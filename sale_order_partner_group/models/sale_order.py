###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_group_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner group',
    )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        partner = self.partner_id.commercial_partner_id
        self.partner_group_id = partner.partner_group_id
        if partner.partner_group_id and partner.is_group_invoice:
            self.partner_invoice_id = partner.partner_group_id
