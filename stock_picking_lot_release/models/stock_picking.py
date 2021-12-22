###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_reset_lots(self):
        if self.picking_type_id.code in ['incoming', 'internal']:
            raise UserError(_(
                'It is not allowed to release lots on the incoming and '
                'internal stock pickings.'))
        if self.state in ['draft', 'confirmed', 'assigned']:
            self.mapped('move_lines').mapped('move_line_ids').write({
                'lot_id': None,
                'lot_name': '',
            })
        return True
