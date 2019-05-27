# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class WizCreateInvoice(models.TransientModel):
    _name = 'wiz.print.options.account.subvention.report'
    _description = 'Wizard to report subvention'

    trimester = fields.Selection(
        selection=[
            (1, 'Trimester 1'),
            (2, 'Trimester 2'),
            (3, 'Trimester 3'),
            (4, 'Trimester 4'),
        ],
        default=1,
        required=1,
    )

    fiscal_year = fields.Many2one('account.fiscalyear', required=1)

    def get_report_formats(self):
        report_ids = self.env['ir.actions.report.xml'].search([])
        return self.env['ir.actions.report.xml'].browse(report_ids)

    @api.multi
    def button_print(self):
        context = self.env.context
        objects = (
            context['active_model'] and context['active_ids'] and
            self.env[context['active_model']].browse(
                context['active_ids']) or [])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': ('account_subvention.subvention_report'),
            'datas': dict(
                ids=objects.ids, trimester=self.trimester,
                target_year=int(self.fiscal_year.date_start[0:4]))}
