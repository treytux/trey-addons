###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    @api.model
    def _get_move_internal_domain(self):
        return [('picking_id.picking_type_id.code', '=', 'internal')]

    move_internal_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='fsm_order_id',
        string='Internal operations',
        domain=_get_move_internal_domain,
    )
    internal_count = fields.Integer(
        string='Internals pickings',
        compute='_compute_picking_ids',
    )

    def action_view_internal(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        internal_ids = [
            picking.id for picking in pickings if
            picking.picking_type_id.code == 'internal']
        if len(internal_ids) > 1:
            action['domain'] = [('id', 'in', internal_ids)]
        elif pickings:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = internal_ids[0]
        return action

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        super()._compute_picking_ids()
        for order in self:
            order.internal_count = len([
                picking for picking in order.picking_ids if
                picking.picking_type_id.code == 'internal'])
