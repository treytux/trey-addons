# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _, exceptions
import logging

_log = logging.getLogger(__name__)


class PrintOptionsCostSimulator(models.TransientModel):
    _name = 'wiz.print.options.cost.simulator'
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

        # cr, uid, context = self.env.args
        # objects = (
        #     context and context['active_model'] and context['active_ids'] and
        #     self.env[context['active_model']].browse(
        #           context['active_ids']) or [])

        # Here you filter report to show depending options
        # if self.option1 == 'value1':
        #     report_name = 'sale.report_saleorder'

        # Return report and datas (dictionary with ids and others values to
        # catch in parser report)
        # return {
        #     'type': 'ir.actions.report.xml',
        #     'report_name': report_name,
        #     'datas': dict(ids=objects.ids, option1=self.option1)}
