###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    show_qty_total = fields.Boolean(
        string='Show quantity total',
        help='Corresponding report print formats module must be installed',
    )
