###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_propagated_comment = fields.Text(
        string='Sale Propagated Comment',
    )
