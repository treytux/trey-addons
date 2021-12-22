###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PrintOptionsSaleCostSimulator(models.TransientModel):
    _name = 'print.options.sale.cost.simulator'
    _description = 'Prints according to options selected.'

    name = fields.Char(
        string='Empty',
    )

    @api.multi
    def button_print(self):
        # Delete raise exception when define option fields in wizard and
        # uncomment text below
        raise ValidationError(_(
            'You must define options fields for this wizard and report to '
            'return.'))
