# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError


class StockInventoryLink(models.TransientModel):
    _name = 'stock.inventory.link'
    _description = 'Wizard to link inventories'

    strategy = fields.Selection(
        selection=[
            ('none', 'Not allow duplicate lines'),
            ('more_recent', 'Recently line'),
            ('add', 'Add quantities'),
        ],
        string='Duplicate lines strategy',
        default='none',
    )

    def link_stock_locations(self, inventory_ids):
        lines_group = {}
        for inventory in inventory_ids:
            for line in inventory.line_ids:
                key = '%s:%s:%s' % (
                    line.location_id.id,
                    line.product_id.id,
                    line.prod_lot_id.id)
                lines_group.setdefault(key, self.env['stock.inventory.line'])
                lines_group[key] |= line
        for key, lines in lines_group.iteritems():
            if self.strategy == 'add':
                lines[0].write({
                    'inventory_id': inventory_ids[0].id,
                    'product_qty': sum(lines.mapped('product_qty')),
                })
                lines[1:].unlink()
            elif self.strategy == 'none':
                if len(lines) != 1:
                    raise UserError(
                        _('Found duplicate lines between inventories!'))
                lines[0].inventory_id = inventory_ids[0]
            elif self.strategy == 'more_recent':
                lines[0].inventory_id = inventory_ids[0]
                lines[1:].unlink()
        inventory_ids[1:].unlink()

    @api.multi
    def button_accept(self):
        active_ids = self.env.context.get('active_ids', [])
        if len(active_ids) < 2:
            raise UserError(_('Required almost two inventories'))
        inventory_ids = self.env['stock.inventory'].search([
            ('id', 'in', active_ids),
        ], order='date desc')
        self.link_stock_locations(inventory_ids)
        return {'type': 'ir.actions.act_window_close'}
