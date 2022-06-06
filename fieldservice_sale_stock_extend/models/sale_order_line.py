###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _field_create_fsm_order_prepare_values(self):
        self.ensure_one()
        res = super()._field_create_fsm_order_prepare_values()
        res['warehouse_id'] = self.order_id.warehouse_id.id
        return res
