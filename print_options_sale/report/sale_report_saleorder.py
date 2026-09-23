###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportSaleOrderPrintOptions(models.AbstractModel):
    _name = 'report.sale.report_saleorder'
    _description = 'Quotation / Order Report With Print Options'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        order_ids = docids or data.get('order_ids')
        orders = self.env['sale.order'].browse(order_ids)
        return {
            'doc_ids': orders.ids,
            'doc_model': 'sale.order',
            'docs': orders,
            'print_option': data.get('print_option'),
        }
