###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api, fields


class StockInventoryLinesSort(models.TransientModel):
    _name = 'stock.inventory.lines.sort'

    method = fields.Selection(
        selection=[
            ('product_name', 'Product name'),
            ('product_code', 'Product code'),
            ('location_name', 'Location')],
        string='Sort lines by',
        default='product_name')
    direction = fields.Selection(
        selection=[
            ('asc', 'Ascending'),
            ('desc', 'Descending')],
        string='direction',
        default='asc')

    @api.multi
    def button_accept(self):
        lines = self.env['stock.inventory.line'].search(
            [('inventory_id', 'in', self.env.context['active_ids'])],
            order='%s %s' % (self.method, self.direction))
        for index, line in enumerate(lines):
            line.sequence = index * 10
