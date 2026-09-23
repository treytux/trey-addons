###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    _sql_constraints = [
        ('unique_number', 'Check(1=1)', 'Account Number can be duplicate'),
    ]
