###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class QcInspection(models.Model):
    _inherit = 'qc.inspection'

    @api.multi
    def object_selection_values(self):
        res = super().object_selection_values()
        res.extend([('stock.production.lot', 'Lot')])
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for inspection in self:
            lot = inspection.lot_id
            if inspection.object_id._name == 'stock.production.lot' and (
                lot.product_id.product_tmpl_id.use_management and (
                    inspection.success)):
                lot.times_used = 0
        return res

    def action_approve(self):
        res = super().action_approve()
        for inspection in self:
            if inspection.product_id.product_tmpl_id.use_management and (
                inspection.object_id._name == 'stock.production.lot' and (
                    inspection.success)):
                inspection.lot_id.times_used = 0
        return res
