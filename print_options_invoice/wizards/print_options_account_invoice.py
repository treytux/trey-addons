###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PrintOptionsAccountInvoice(models.TransientModel):
    _name = 'print.options.account.invoice'
    _description = 'Prints according to options selected.'

    name = fields.Char(
        string='Empty',
    )

    @api.multi
    def button_print(self):
        raise ValidationError(_(
            'You must define options fields for this wizard and report to '
            'return.'))
