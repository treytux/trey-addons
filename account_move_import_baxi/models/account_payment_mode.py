###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    baxi_name = fields.Char(
        string='Baxi name',
        help='This field is used for map payments mode when import Baxi '
             'invoices. You can put several names separated by commas.',
    )
