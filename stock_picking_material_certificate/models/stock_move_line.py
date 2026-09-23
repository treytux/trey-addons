###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    certificate_number = fields.Char(
        string='Certificate number',
    )

    @api.onchange('lot_name', 'lot_id')
    def onchange_serial_number(self):
        res = super().onchange_serial_number()
        if self.lot_id and self.lot_id.certificate_number:
            self.certificate_number = self.lot_id.certificate_number
        return res

    def _action_done(self):
        res = super()._action_done()
        for move_line in self.exists():
            if move_line.lot_id and move_line.certificate_number:
                lot = move_line.lot_id
                lot.certificate_number = move_line.certificate_number
        return res
