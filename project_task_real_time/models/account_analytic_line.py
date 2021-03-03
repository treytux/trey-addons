###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    real_time = fields.Float(
        string='Real time',
    )
