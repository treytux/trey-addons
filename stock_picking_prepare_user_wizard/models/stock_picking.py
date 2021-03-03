###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Prepare user',
    )

    @api.multi
    def do_print_picking(self):
        if self.user_id or len(self) != 1:
            return super().do_print_picking()
        if self.picking_type_code != 'outgoing':
            return super().do_print_picking()
        if self.state in ['done', 'cancel']:
            return super().do_print_picking()
        if self._context.get('force_button_print'):
            return super().do_print_picking()
        wizard = self.env['stock.picking.prepare_user'].create({
            'picking_id': self.id,
        })
        action = self.env.ref(
            'stock_picking_prepare_user_wizard.'
            'stock_picking_prepare_user_action').read()[0]
        action['res_id'] = wizard.id
        ctx = self._context.copy()
        ctx['force_button_print'] = True
        action['context'] = ctx
        return action
