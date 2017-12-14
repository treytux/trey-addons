# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class StockPicking(models.TransientModel):
    _name = 'report.stock.report_picking'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        order_obj = self.env['stock.picking']
        report = report_obj._get_report_from_name('stock.report_picking')
        selected_orders = order_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_orders}
        report = report_obj.browse(self.ids[0])
        return report.render('stock.report_picking', docargs)

# class InvoiceReport(models.TransientModel):
#     _inherit = 'report.account.report_invoice'

#     @api.multi
#     def _invoice_line_by_picking(self, invoice):
#         # {u'AC\\OUT\\00001': {'2015-01-02 09:28:51': [3727, 3728, 3729,
#         # 3730, 3731, 3732, 3733, 3734]}, u'AC\\OUT\\00003': {'2015-01-02
#         # 09:35:02': [3735]}, 'NO_VALID': {'NO_DATE': [3726]}}
#         # }
#         dic = {}
#         for line in invoice.invoice_line:
#             if line.origin:
#                 if 'OUT' in line.origin:
#                     picking_ids = self.env['stock.picking'].search(
#                         [('name', '=', line.origin)])
#                     if line.origin not in dic:
#                         dic[line.origin] = {}
#                         if not picking_ids:
#                             if 'NO_DATE' not in dic[line.origin]:
#                                 dic[line.origin]['NO_DATE'] = []
#                             dic[line.origin]['NO_DATE'].append(line.id)
#                         else:
#                             picking = self.env['stock.picking'].browse(
#                                 picking_ids[0])
#                             if picking.date_done not in dic[line.origin]:
#                                 dic[line.origin][picking.date_done] = []
#                             dic[line.origin][picking.date_done].append(
# line.id)
#                     else:
#                         picking = self.env['stock.picking'].browse(
#                             picking_ids[0])
#                         dic[line.origin][picking.date_done].append(line.id)
#                 elif 'OUT' not in line.origin:
#                     if 'NO_VALID' not in dic:
#                         dic['NO_VALID'] = {}
#                         if 'NO_DATE' not in dic['NO_VALID']:
#                             dic['NO_VALID']['NO_DATE'] = []
#                     dic['NO_VALID']['NO_DATE'].append(line.id)
#             else:
#                 if 'NO_VALID' not in dic:
#                     dic['NO_VALID'] = {}
#                     if 'NO_DATE' not in dic['NO_VALID']:
#                         dic['NO_VALID']['NO_DATE'] = []
#                 dic['NO_VALID']['NO_DATE'].append(line.id)
#         return dic

#     @api.multi
#     def render_html(self, data=None):
#         report_obj = self.env['report']
#         invoice_obj = self.env['account.invoice']
#         report = report_obj._get_report_from_name('account.report_invoice')
#         selected_invoices = invoice_obj.browse(self.ids)
#         docargs = {
#             'doc_ids': self.ids,
#             'doc_model': report.model,
#             'docs': selected_invoices,
#             'get_tax_description': partial(self.get_tax_description),
#             'get_taxes': partial(self.get_taxes),
#             'invoice_line_by_picking': partial(
#               self._invoice_line_by_picking)}
#         report = report_obj.browse(self.ids[0])
#         return report.render('account.report_invoice', docargs)
