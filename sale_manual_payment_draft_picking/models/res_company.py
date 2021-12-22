###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    manual_payment_picking_state = fields.Selection(
        string='Picking state',
        selection=[
            ('unlocked', 'Unlocked'),
            ('draft', 'Draft'),
        ],
        required=True,
        default='unlocked',
    )
    manual_payment_state = fields.Selection(
        string='Payment state',
        selection=[
            ('authorized', 'Authorized'),
            ('done', 'Done'),
        ],
        required=True,
        default='done',
    )
