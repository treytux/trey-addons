###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class StockQuantPackageCreate(models.TransientModel):
    _name = 'stock.quant.package.create'
    _description = 'Create stock package'

    def _get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    package_id = fields.Many2one(
        comodel_name='stock.quant.package',
        string='Package',
    )
    name = fields.Char(
        string='Pack name',
        required=True,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location dest',
        required=True,
        domain='[("usage", "=", "internal")]',
        default=_get_default_location_id,
    )
    line_ids = fields.One2many(
        comodel_name='stock.quant.package.create_line',
        inverse_name='wizard_id',
        string='Lines',
    )

    def action_confirm(self):
        pack = self.package_id
        if not pack:
            pack = self.env['stock.quant.package'].create({
                'name': self.name,
            })
        warehouse = self.location_id.get_warehouse()
        origin = _('Package %s creation') % self.name
        picking = self.env['stock.picking'].create({
            'move_type': 'direct',
            'origin': origin,
            'partner_id': self.env.user.company_id.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
            'picking_type_id': warehouse.int_type_id.id,
        })
        move_obj = self.env['stock.move']
        moves_group = {}
        for line in self.line_ids:
            if not line.product_qty:
                continue
            qty_factor = line.packaging_id and line.packaging_id.qty or 1
            moves_group[line.id] = move_obj.create({
                'origin': origin,
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': qty_factor * line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': line.location_id.id,
                'location_dest_id': self.location_id.id,
                'product_packaging': line.packaging_id.id,
            })
        picking.action_confirm()
        picking.action_assign()
        for line in self.line_ids:
            move = moves_group[line.id]
            move_line = picking.move_line_ids.filtered(
                lambda ln: ln.move_id == move)
            qty_factor = line.packaging_id and line.packaging_id.qty or 1
            move_line.write({
                'result_package_id': pack.id,
                'qty_done': qty_factor * line.product_qty,
                'lot_id': line.lot_id.id,
            })
        picking.action_done()
        if picking.state != 'done':
            raise exceptions.ValidationError(_(
                'Not enough stock of some products to finalise the operation'))


class StockQuantPackageCreateLine(models.TransientModel):
    _name = 'stock.quant.package.create_line'
    _description = 'Stock quant package create line'

    def _get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    wizard_id = fields.Many2one(
        comodel_name='stock.quant.package.create',
        string='Wizard',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
        domain='[("usage", "=", "internal")]',
        default=_get_default_location_id,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain='[("type", "in", ["product", "consu"])]',
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial',
        domain='[("product_id", "=", product_id)]',
    )
    product_qty = fields.Float(
        string='Quantity',
    )
    available_qty = fields.Float(
        compute='_compute_available_qty',
        string='Available qty',
    )
    packaging_id = fields.Many2one(
        comodel_name='product.packaging',
        string='Packaging',
    )

    @api.depends('product_id', 'lot_id', 'location_id')
    def _compute_available_qty(self):
        for line in self:
            if not line.product_id:
                line.available_qty = 0
                continue
            product = line.product_id.with_context(
                location=line.location_id.id,
                lot_id=line.lot_id.id,
            )
            line.available_qty = product.qty_available

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.lot_id.product_id != self.product_id:
            self.lot_id = False

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id.id
