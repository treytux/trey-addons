# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions


class PrintOptionsSaleCostSimulator(models.TransientModel):
    _name = 'wiz.print.options.sale.cost.simulator'
    _description = 'Prints according to options selected.'

    name = fields.Char(string='Empty')

    # option1 = fields.Selection(
    #     selection=[
    #         ('value1', 'Text1'),
    #         ('value2', 'Text2')],
    #     string='Option 1',
    #     default='value1')

    @api.multi
    def button_print(self):
        # Delete raise exception when define option fields in wizard and
        # uncomment text below
        raise exceptions.Warning(_(
            'You must define options fields for this wizard and report to '
            'return.'))
