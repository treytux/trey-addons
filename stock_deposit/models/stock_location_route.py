###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    create_deposit_rules = fields.Boolean(
        string='Create deposit rules',
        help='If this option is checked, when creating a new stock deposit '
             'from the "Create deposit" wizard, a rule for this route will be '
             'automatically created.',
    )
