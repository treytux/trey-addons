###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplierinfo_delay = fields.Integer(
        string='Supplierinfo delay',
        default=7,
        help='Delay to be assigned automatically in the product supplierinfo '
             'records when the supplier is added.',
    )
    factor_min_stock = fields.Float(
        string='Factor min stock',
        default=1,
        help='This factor is used for the calculation of the minimum quantity '
             'of the warehouse orderpoints.'
    )
    factor_max_stock = fields.Float(
        string='Factor max stock',
        default=1,
        help='This factor is used for the calculation of the maximum quantity '
             'of the warehouse orderpoints.'
    )
