###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        re = super().create(vals)
        if 'date_planned' in vals:
            re.date_planned = vals['date_planned']
        return re
