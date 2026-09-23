###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def select_websites(self):
        return self.env['website'].search([
            ('is_woo', '=', True),
            ('woo_sync_stock_realtime', '=', True),
            ('woo_export_method', '!=', 'manual'),
        ])

    @api.model
    def create(self, vals):
        move = super().create(vals)
        for website in self.select_websites():
            move.product_id.woo_upload(website, ['qty_available'])
        return move

    def write(self, vals):
        move = super().write(vals)
        for website in self.select_websites():
            for record in self:
                record.product_id.woo_upload(website, ['qty_available'])
        return move

    def unlink(self):
        move = super().unlink()
        for website in self.select_websites():
            for record in self:
                record.product_id.woo_upload(website, ['qty_available'])
        return move
