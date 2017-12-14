# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_print_options_stock_picking(self):
        wiz = self.env['wiz.print.options.stock.picking'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.print.options.stock.picking',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new'}
