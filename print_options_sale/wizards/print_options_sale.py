###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WizPrintOptionsSale(models.TransientModel):
    _name = 'wiz.print.options.sale'
    _description = 'Prints according to options selected.'

    print_option = fields.Selection(
        selection=[
            ('with_prices', 'With prices'),
            ('without_prices', 'Without prices'),
        ],
        string='Print option',
        default='with_prices',
        required=True,
    )

    def button_print(self):
        active_ids = self.env.context.get('active_ids', [])
        orders = self.env['sale.order'].browse(active_ids)
        report = self.env.ref('sale.action_report_saleorder')
        return report.report_action(
            orders, data={
                'print_option': self.print_option,
                'order_ids': orders.ids,
            }, config=False)
