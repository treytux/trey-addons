###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_position_purchase_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        company_dependent=True,
        string='Fiscal position purchases',
        help='The fiscal position determines the taxes/accounts used for this '
             'contact in purchases.',
    )
