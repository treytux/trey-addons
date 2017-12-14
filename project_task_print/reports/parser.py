# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class ProjectTaskReport(models.TransientModel):
    _name = 'report.project_task_print.report_project_task'

    # IMPORTANTE: Revisar los métodos de la clase para comprobar su utilidad
    # @api.multi
    # def get_tax_description(self, tax_line_name):
    #     tax_line_name_parts = tax_line_name.split('-')
    #     if len(tax_line_name_parts) > 0:
    #         return tax_line_name_parts[0]
    #     else:
    #         return tax_line_name

    # @api.multi
    # def get_taxes(self, order):
    #     taxes = {}
    #     for line in order.order_line:
    #         for tax in line.tax_id:
    #             t = tax.compute_all(
    #                 line.price_unit * (1 - (line.discount or 0.0) / 100.0),
    #                 line.product_uom_qty,
    #                 line.product_id,
    #                 line.order_id.partner_id
    #             )['taxes']
    #             if len(t) > 0 and t[0]['name'] not in taxes:
    #                 taxes[t[0]['name']] = 0
    #             taxes[t[0]['name']] += t[0]['amount']
    #     return taxes

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        task_obj = self.env['project.task']
        report = report_obj._get_report_from_name(
            'project_task_print.report_project_task')
        seleted_tasks = task_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': seleted_tasks,
            # 'get_tax_description': partial(self.get_tax_description),
            # 'get_taxes': partial(self.get_taxes)
        }
        report = report_obj.browse(self.ids[0])
        return report.render('project_task_print.report_project_task', docargs)
