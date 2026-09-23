###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tbai_third_party = fields.Boolean(
        string='Presentation of TicketBai by third parties',
    )
