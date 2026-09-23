###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class PrintOptionsSaleCostSimulator(models.TransientModel):
    _name = 'wiz.print.options.sale.cost.simulator'
    _description = 'Prints according to options selected.'

    name = fields.Char(
        string='Empty',
    )

    def button_print(self):
        raise UserError(_(
            'You must define options fields for this wizard and report to '
            'return.'))
