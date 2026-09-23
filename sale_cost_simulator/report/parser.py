##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial

from odoo import api, models


class SaleCostSimulator(models.AbstractModel):
    _name = 'report.sale_cost_simulator.report_sale_simulation'
    _description = 'Sale cost simulation report'

    def get_xml_id(self, module, res_id):
        ir_model_datas = self.env['ir.model.data'].search([
            ('res_id', '=', res_id),
            ('module', '=', module),
            ('model', '=', 'res.company'),
        ])
        return ir_model_datas and ir_model_datas[0].name or None

    @api.model
    def _get_report_values(self, docids, data=None):
        selected_orders = self.env['sale.cost.simulator'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.cost.simulator',
            'docs': selected_orders,
            'data': data,
            'get_xml_id': partial(self.get_xml_id),
        }
