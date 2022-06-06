###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockInventoryProduct(models.TransientModel):
    _name = 'stock.inventory.product'
    _description = 'Wizard to add products to inventory'

    name = fields.Char(
        string='Inventory name',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
    )
    line_ids = fields.One2many(
        comodel_name='stock.inventory.product.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'location_id' not in res:
            location_id = self.env['stock.inventory']._default_location_id()
            res['location_id'] = location_id
        if 'line_ids' not in res:
            res['line_ids'] = []
        products = self.env['product.product'].browse(
            self.env.context.get('active_ids', []))
        for product in products:
            line = {
                'wizard_id': self.id,
                'product_id': product.id,
                'barcode': product.barcode,
                'qty_available': 0,
                'theoretical_available': product.with_context(
                    location=location_id).qty_available,
            }
            res['line_ids'].append((0, 0, line))
        return res

    @api.multi
    def button_create_stock_inventory(self):
        inventory = self.env['stock.inventory'].create({
            'name': 'INV: ' + fields.Datetime.now().strftime('%Y%m%d%H%M%S'),
            'filter': 'partial',
            'location_id': self.location_id.id,
            'exhausted': True,
            'date': fields.Datetime.now(),
        })
        for line in self.line_ids:
            inventory.line_ids.create({
                'inventory_id': inventory.id,
                'product_id': line.product_id.id,
                'theoretical_qty': line.theoretical_available,
                'product_qty': line.qty_available,
                'location_id': self.location_id.id,
            })
        return self._reopen_view(inventory)

    def _reopen_view(self, inventory):
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.inventory',
            'res_id': inventory.id,
            'view_id': self.env.ref('stock.view_inventory_form').id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class StockInventoryProductLine(models.TransientModel):
    _name = 'stock.inventory.product.line'
    _description = 'Wizard line'

    name = fields.Char(
        string='Empty',
    )
    wizard_id = fields.Many2one(
        comodel_name='stock.inventory.product',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    barcode = fields.Char(
        related='product_id.barcode',
        string='Barcode',
    )
    theoretical_available = fields.Float(
        compute='_compute_theoretical_available',
        string='Theoretical quantity'
    )
    qty_available = fields.Float(
        string='Available quantity'
    )

    @api.one
    @api.depends('wizard_id.location_id', 'product_id')
    def _compute_theoretical_available(self):
        self.theoretical_available = self.product_id.with_context(
            location=self.wizard_id.location_id.id).qty_available
