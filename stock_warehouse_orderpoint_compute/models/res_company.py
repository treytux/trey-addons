###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_delay = fields.Integer(
        string='Delay',
        default=1,
        required=True,
        help='Generic delivery lead time for the calculation of minimum and '
             'maximum quantities in the warehouse orderpoints in case the '
             'associated product has not a supplier defined.',
    )
    stock_period = fields.Integer(
        string='Period',
        default=30,
        required=True,
        help='Period of time for which the calculation of the minimum and '
             'maximum quantities of the warehouse orderpoints will be carried '
             'out.\n'
             'Example: if the period is defined at "30", the calculation will '
             'be made using "today - 30 days" as the starting date and '
             '"today" as the ending date.',
    )

    @api.constrains('stock_delay')
    def check_stock_delay(self):
        for company in self:
            if company.stock_delay <= 0:
                raise ValidationError(_(
                    'The \'Delay\' field must be greater than 0.'))

    @api.constrains('stock_period')
    def check_stock_period(self):
        for company in self:
            if company.stock_period <= 0:
                raise ValidationError(_(
                    'The \'Period\' field must be greater than 0.'))
