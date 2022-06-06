###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _field_create_fsm_order_prepare_values(self):
        res = super()._field_create_fsm_order_prepare_values()
        self.ensure_one()
        lines = self.order_line.filtered(
            lambda sol: sol.product_id.field_service_tracking == 'sale')
        templates = lines.mapped('product_id.fsm_order_template_id')
        order_activity_ids = self.env['fsm.activity']
        for template in templates:
            order_activity_ids |= template.temp_activity_ids
        res['order_activity_ids'] = [(6, 0, order_activity_ids.ids)]
        if len(templates) == 1:
            res['template_id'] = templates.id
        return res
