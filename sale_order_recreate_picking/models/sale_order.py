###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    not_recreate_picking = fields.Boolean(
        string='Not Recreate Picking',
        compute='_compute_not_recreate_picking',
        compute_sudo=True,
    )

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_not_recreate_picking(self):
        for order in self:
            if order.mapped('picking_ids').filtered(
                    lambda p: p.state not in ('done', 'cancel')):
                order.not_recreate_picking = True
            else:
                order.not_recreate_picking = False

    def action_recreate_picking(self):
        for sale in self:
            if sale.state != 'sale' or sale.not_recreate_picking:
                raise UserError(_(
                    'Order State not in sale or pending picking'))
            sale._action_confirm()
