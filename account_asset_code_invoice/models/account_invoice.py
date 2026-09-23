###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_asset_code_from_invoice(self, asset):
        move_lines = self.env['account.move.line'].search([
            ('asset_id', '=', asset.id),
        ])
        product = move_lines.mapped('product_id')
        invoice_line = self.invoice_line_ids.filtered(
            lambda ln: ln.product_id == product)
        line_id = invoice_line[0].id % 100
        return '%s-%s' % (self.number, line_id)

    @api.multi
    def action_invoice_open(self):
        res = super().action_invoice_open()
        for invoice in self:
            assets = invoice.move_id.line_ids.mapped('asset_id')
            for asset in assets:
                asset.code = invoice.get_asset_code_from_invoice(asset)
                for line in asset.depreciation_line_ids[1:]:
                    seq = line.name.split('/')[1]
                    line.name = asset._get_depreciation_entry_name(seq)
        return res
