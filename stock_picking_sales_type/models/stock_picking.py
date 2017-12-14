# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_type_id = fields.Many2one(
        comodel_name='sale.order.type',
        string='Sale Type',
        compute="_calculate_sale_type",
        store=True)

    @api.one
    @api.depends('group_id', 'sale_id',)
    def _calculate_sale_type(self):
        if self.group_id:
            sale = self.env['sale.order'].search([
                ('procurement_group_id', '=', self.group_id.id)], limit=1)
            self.sale_type_id = sale.type_id.id
