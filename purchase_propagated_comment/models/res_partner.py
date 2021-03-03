###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_propagated_comment = fields.Text(
        string='Purchase Propagated Comment',
    )
