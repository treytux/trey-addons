###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_barcode_scan_dummy_label(self):
        def atoi_code(text):
            return int(text) if text.isdigit() else text

        def natural_keys(text):
            return [atoi_code(c) for c in re.split('(\\d+)', text)]

        module_name = 'stock_barcodes_dummy_label'
        action_name = 'stock_barcodes_dummy_label_wizard_action'
        action = self.env.ref('%s.%s' % (module_name, action_name)).read()[0]
        wizard = self.env['stock.barcodes.dummy.label'].create({})
        lines = self.env['stock.barcodes.dummy.label.line']
        confirm_lines = self.env['stock.barcodes.dummy.confirm']
        log_lines = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', self.id),
            ('active', '=', True),
        ])
        move_lines_to_show = self.move_lines
        for line in move_lines_to_show:
            if line.reserved_availability <= 0:
                move_lines_to_show -= line
        code_list = move_lines_to_show.mapped('product_id.default_code')
        if not all(code_list):
            raise UserError(_(
                  'Some products do not have a default code assigned.'))
        code_list.sort(key=natural_keys)
        for code in code_list:
            moves = self.move_lines.filtered(
                lambda m: m.product_id.default_code == code)
            qty_res = sum(moves.mapped('product_uom_qty')) - sum(
                moves.mapped('quantity_done'))
            if qty_res == 0:
                continue
            logs = log_lines.filtered(
                lambda ln: ln.product_id == moves[0].product_id)
            qty_logs = sum(logs.mapped('qty'))
            if qty_logs <= qty_res:
                for line in logs:
                    confirm_data = {
                        'wizard_id': wizard.id,
                        'barcode': line.barcode,
                        'product_id': line.product_id.id,
                        'lot_id': line.lot_id and line.lot_id.id or False,
                        'qty': line.qty,
                        'dummy_id': line.dummy_id.id,
                        'pallet_barcode': line.pallet_barcode,
                    }
                    confirm_lines |= confirm_lines.create(confirm_data)
            qty_res = qty_res - qty_logs
            line_data = {
                'wizard_id': wizard.id,
                'product_id': moves[0].product_id.id,
                'qty': qty_res,
            }
            lines |= lines.create(line_data)
        wizard.write({
            'picking_id': self.id,
            'partner_id': self.partner_id.id,
            'partner_ref': self.partner_id.ref,
            'partner_address': self.partner_id._display_address(),
            'line_ids': [(6, 0, lines.ids)],
            'confirm_line_ids': [(6, 0, confirm_lines.ids)],
        })
        action['res_id'] = wizard.id
        return action

    def button_unlink_stock_barcodes_dummy_log(self):
        module_name = 'stock_barcodes_dummy_label'
        action_name = 'stock_barcodes_dummy_remove_logs_wizard_action'
        action = self.env.ref('%s.%s' % (module_name, action_name)).read()[0]
        wizard = self.env['stock.barcodes.dummy.remove.logs'].create({
            'picking_id': self.id,
        })
        action['res_id'] = wizard.id
        return action
