# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp.osv import osv


class Contract1Report(osv.AbstractModel):
    _name = 'report.print_contract_report.contract1'

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        analytic_acc_obj = self.pool['account.analytic.account']
        report = report_obj._get_report_from_name(
            cr, uid, 'print_contract_report.contract1')
        selected_orders = analytic_acc_obj.browse(cr, uid, ids,
                                                  context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': selected_orders,
        }

        return report_obj.render(
            cr, uid, ids,
            'print_contract_report.contract1', docargs,
            context=context
        )


class Contract2Report(osv.AbstractModel):
    _name = 'report.print_contract_report.contract2'

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        analytic_acc_obj = self.pool['account.analytic.account']
        report = report_obj._get_report_from_name(
            cr, uid, 'print_contract_report.contract2')
        selected_orders = analytic_acc_obj.browse(cr, uid, ids,
                                                  context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': selected_orders,
        }

        return report_obj.render(
            cr, uid, ids,
            'print_contract_report.contract2', docargs,
            context=context
        )


class SaleContractReport(osv.AbstractModel):
    _name = 'report.print_contract_report.sale_contract'

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        sale_order = self.pool['sale.order']

        res = ''
        for order in sale_order.browse(cr, uid, ids, context=context):
            # Presupuesto
            res += report_obj.get_html(
                cr, uid, ids, 'sale.report_saleorder', data=data,
                context=context)

            # Contrato
            if order.contract_type_id and order.contract_type_id.report_id:
                report_name = (
                    'report.' + order.contract_type_id.report_id.report_file)
                res += self.pool[report_name].render_html(
                    cr, uid, ids, data, context)

        return res
