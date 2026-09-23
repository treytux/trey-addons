###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_group_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner group',
        compute='_compute_partner_group_id',
    )

    @api.depends('partner_id')
    def _compute_partner_group_id(self):
        for sale in self:
            partner = sale.partner_id.commercial_partner_id
            sale.partner_group_id = partner.partner_group_id
            if partner.partner_group_id and partner.is_group_invoice:
                sale.partner_invoice_id = partner.partner_group_id
