###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_planned_public = fields.Boolean(
        string='Date planned public in Website',
        default=True)
