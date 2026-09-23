###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportSaleCommissionInvoice(models.AbstractModel):
    _name = 'report.sale_commission_report.report_settlement_invoice'
    _description = 'Settlement by Invoice Report'

    def get_lines_grouped(self, settlement):
        inv_list = []
        invoices = settlement.mapped('lines.invoice')
        for invoice in invoices:
            inv_lines = settlement.lines.filtered(
                lambda ln: ln.invoice == invoice)
            inv_subtotal = sum(inv_lines.mapped('settled_amount'))
            inv_list.append({
                'invoice': invoice,
                'lines': inv_lines,
                'subtotal': inv_subtotal,
            })
        return inv_list

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.commission.settlement'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.commission.settlement',
            'docs': docs,
            'lines_grouped': self.get_lines_grouped,
        }
