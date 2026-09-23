###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_policy = fields.Selection(
        selection_add=[
            ('all_delivered', 'All delivered'),
        ],
    )
