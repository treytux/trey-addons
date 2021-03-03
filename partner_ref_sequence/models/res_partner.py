###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if 'ref' not in vals:
            vals['ref'] = self.env['ir.sequence'].next_by_code(
                'res.partner.ref')
        return super().create(vals)
