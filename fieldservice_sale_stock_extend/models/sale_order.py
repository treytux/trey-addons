###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _field_create_fsm_order_prepare_values(self):
        self.ensure_one()
        res = super()._field_create_fsm_order_prepare_values()
        res['warehouse_id'] = self.warehouse_id.id
        return res

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for sale in self:
            out_pickings = sale.picking_ids.filtered(
                lambda p: p.picking_type_code == 'outgoing' and p.fsm_order_id)
            out_pickings.do_unreserve()
            for picking in out_pickings:
                picking.action_toggle_is_locked()
                picking_msg = _(
                    '''This picking is waiting the assignment of technician,
                       vehicle and warehouse in the field service order:
                       <a href=# data-oe-model=fsm.order data-oe-id=%d>%s</a>
                    ''') % (picking.fsm_order_id.id, picking.fsm_order_id.name)
                picking.message_post(body=picking_msg)
        return res
