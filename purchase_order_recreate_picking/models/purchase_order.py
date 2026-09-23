###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    not_recreate_picking = fields.Boolean(
        string='Not recreate picking',
        compute='_compute_not_recreate_picking',
        compute_sudo=True,
    )

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_not_recreate_picking(self):
        for order in self:
            order.not_recreate_picking = bool(order.picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel')))

    def action_recreate_picking(self):
        for purchase in self:
            if purchase.state != 'purchase' or purchase.not_recreate_picking:
                raise UserError(_(
                    'Order state not in purchase or pending picking'))
            purchase.with_context(recreate_picking=True)._create_picking()
