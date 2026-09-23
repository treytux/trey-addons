###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models

REPORT_XMLID_BY_OPTION = {
    'with_payments': 'account.account_invoices',
    'without_payments': 'account.account_invoices_without_payment',
}


class WizPrintOptionsInvoice(models.TransientModel):
    _name = 'wiz.print.options.invoice'
    _description = 'Prints invoice according to options selected.'

    print_option = fields.Selection(
        selection=[
            ('with_payments', 'With payment info'),
            ('without_payments', 'Without payment info'),
        ],
        string='Print option',
        default='with_payments',
        required=True,
    )

    def button_print(self):
        active_ids = self.env.context.get('active_ids', [])
        moves = self.env['account.move'].browse(active_ids)
        report = self.env.ref(REPORT_XMLID_BY_OPTION[self.print_option])
        return report.report_action(moves, config=False)
