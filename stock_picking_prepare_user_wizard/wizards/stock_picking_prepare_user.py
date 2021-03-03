###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicingPrepareUser(models.TransientModel):
    _name = 'stock.picking.prepare_user'
    _description = 'Stock picking prepare user wizard'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Prepare user',
        default=lambda self: self.env.user.id,
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )

    def action_assign_prepare_user(self):
        self.ensure_one()
        assert self.picking_id, 'You must create the wizard with a picking'
        self.picking_id.user_id = self.user_id.id
        return self.picking_id.with_context(
            force_button_print=True).do_print_picking()
