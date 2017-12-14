# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from functools import partial


class SaleCostSimulator(models.TransientModel):
    _name = 'report.sale_cost_simulator.report_sale_simulation'

    @api.multi
    def get_xml_id(self, module, res_id):
        ir_model_datas = self.env['ir.model.data'].search([
            ('res_id', '=', res_id),
            ('module', '=', module),
            ('model', '=', 'res.company')])
        return ir_model_datas and ir_model_datas[0].name or None

    @api.multi
    def render_html(self, data=None):
        template = 'sale_cost_simulator.report_sale_simulation'
        doc = self.env['report']._get_report_from_name(template)
        selected_orders = self.env['simulation.cost'].browse(self.ids)
        report = self.env['report'].browse(self.ids[0])
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': doc.model,
            'docs': selected_orders,
            'data': data and data or None,
            'get_xml_id': partial(self.get_xml_id)})
