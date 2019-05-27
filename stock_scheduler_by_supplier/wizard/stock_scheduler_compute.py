###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class StockSchedulerCompute(models.TransientModel):
    _inherit = 'stock.scheduler.compute'

    supplier_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='scheduler_supplier_relation',
        column1='partner_id',
        column2='compute_id',
        string='Suppliers')

    @api.multi
    def procure_calculation(self):
        if not self.supplier_ids:
            return super().procure_calculation()
        op_ids = self.env['stock.warehouse.orderpoint'].search([
            ('seller_ids.name', 'in', self.supplier_ids.ids)])
        return super().with_context(
            orderpoint_ids=op_ids.ids,
            suppliers=self.supplier_ids)._procure_calculation_orderpoint()
