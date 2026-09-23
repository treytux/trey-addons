###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportStockPicking(models.AbstractModel):
    _name = 'report.stock.picking'
    _description = 'Stock Picking Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        for picking in docs:
            has_discount = any(
                move.sale_line_id.discount > 0
                for move in picking.move_ids
                if move.sale_line_id
            )
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'has_discount': has_discount,
        }
