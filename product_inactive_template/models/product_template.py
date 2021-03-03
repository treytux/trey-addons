###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def write(self, vals):
        if 'active' not in vals:
            return super().write(vals)
        if vals['active'] is False:
            self = self.with_context(ignore_inactive=True)
        return super().write(vals)
