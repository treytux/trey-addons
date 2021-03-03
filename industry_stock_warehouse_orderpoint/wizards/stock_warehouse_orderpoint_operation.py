###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockWarehouseOrderpointOperation(models.TransientModel):
    _name = 'stock.warehouse.orderpoint.operation'
    _description = 'Order Point Operation'

    state = fields.Selection(
        string='Operation',
        selection=[
            ('copy_suggested', 'Copy Suggested Qty to Purchase Qty'),
            ('update_qty_rule', 'Update Qty (Max/Min)'),
            ('make_procurement', 'Generate Procurement Orders'),
            ('update_qty_year', 'Update Qty Min Last Year'),
        ],
        required=True,
        default='copy_suggested',
    )

    @api.multi
    def select_operation_to_run(self):
        active_ids = self.env.context['active_ids']
        ops = self.env['stock.warehouse.orderpoint'].browse(active_ids)
        if self.state == 'copy_suggested':
            ops.compute_copy_product_suggested_qty()
        elif self.state == 'update_qty_rule':
            ops.compute_rule_quantities_from_product_min_qty_year()
        elif self.state == 'update_qty_year':
            ops.compute_product_min_qty_year()
        elif self.state == 'make_procurement':
            ops.make_procurement()
        return
