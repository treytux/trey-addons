###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def action_unbuild(self):
        self.ensure_one()
        mo = self.env['mrp.production'].search([
            ('product_id', '=', self.product_id.id),
            ('state', '=', 'done'),
        ], order='id desc', limit=1)
        if self.lot_id:
            mo = mo.filtered(
                lambda mo: self.lot_id in mo.mapped(
                    'move_finished_ids.move_line_ids.lot_id'))
        if not mo:
            raise UserError(
                self.lot_id and _(
                    'You cannot unbuild a product with a lot that has not '
                    'been previously manufactured.'
                )
                or _(
                    'You cannot unbuild a product that has not been '
                    'previously manufactured.'
                )
            )
        return super().action_unbuild()

    def _generate_move_from_bom_line(self, bom_line, quantity):
        if bom_line.product_id.type == 'service':
            return self.env['stock.move']
        return super(MrpUnbuild, self)._generate_move_from_bom_line(
            bom_line, quantity)
