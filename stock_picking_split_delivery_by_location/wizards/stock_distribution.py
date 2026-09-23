###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockDistribution(models.TransientModel):
    _name = 'stock.distribution'
    _description = 'Wizard to split delivery by location'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    line_ids = fields.One2many(
        comodel_name='stock.distribution.line',
        inverse_name='wizard_id',
        string='Wizard lines',
    )
    confirm_line_ids = fields.One2many(
        comodel_name='stock.distribution.confirm.line',
        inverse_name='wizard_id',
        string='Wizard confirm lines',
    )

    def check_products_qty(self):
        for line in self.confirm_line_ids:
            if line.quantity == 0:
                raise ValidationError(_(
                    'You cannot request zero quantity for product "%s"') % (
                        line.product_id.display_name))
        products = self.confirm_line_ids.mapped('product_id')
        expected_products = self.picking_id.move_ids.mapped('product_id')
        if set(expected_products.ids) != set(products.ids):
            raise ValidationError(_(
                'There are still some products to be allocated in the '
                'distribution. All picking products must be distributed.'))
        for product in products:
            qty_available = self.line_ids.filtered(
                lambda ln: ln.product_id == product)[0].qty_requested
            qty_requested = sum(self.confirm_line_ids.filtered(
                lambda ln: ln.product_id == product).mapped('quantity'))
            if qty_requested > qty_available:
                raise ValidationError(
                    _('The total distributed quantity for product "%s" (%s) '
                      'exceeds the original quantity (%s).') % (
                          product.display_name, qty_requested, qty_available))
            if qty_requested != qty_available:
                raise ValidationError(_(
                    'The quantities to be distributed of product "%s" must '
                    'match the quantities on picking') % product.display_name)
        return True

    def check_products_availability(self):
        for line in self.confirm_line_ids:
            qty_available = line.product_id.with_context(
                location=line.location_id.id).qty_available
            if line.quantity > qty_available:
                raise ValidationError(
                    _('Quantity requested for product "%s" (%s) '
                      'exceeds the available quantity (%s) in "%s".') % (
                          line.product_id.display_name, line.quantity,
                          qty_available, line.location_id.display_name))
        return True

    def get_stock_picking_data(self, picking, picking_type, location_id):
        return {
            'partner_id': picking.partner_id.id,
            'picking_type_id': picking_type[0].id,
            'location_id': location_id,
            'location_dest_id': picking.location_dest_id.id,
            'origin': picking.origin,
        }

    def get_stock_picking_line_data(
            self, line, new_picking, location_id, sale_line):
        return {
            'name': line.product_id.display_name,
            'product_id': line.product_id.id,
            'product_uom_qty': line.quantity,
            'product_uom': line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'location_id': location_id,
            'location_dest_id': new_picking.location_dest_id.id,
            'sale_line_id': sale_line.id,
        }

    def action_confirm_distribution(self):
        self.ensure_one()
        self.check_products_qty()
        self.check_products_availability()
        distribution = {}
        for line in self.confirm_line_ids:
            key = line.location_id.id
            distribution.setdefault(key, []).append(line)
        new_pickings = []
        picking = self.picking_id
        group_id = picking.group_id
        for location_id, lines in distribution.items():
            if location_id == self.picking_id.location_id.id:
                for move in picking.move_ids:
                    move._action_cancel()
                picking.move_ids.unlink()
                picking.group_id = group_id.id
                for line in lines:
                    sale_line = self.picking_id.sale_id.order_line.filtered(
                        lambda ln: ln.product_id == line.product_id)[0]
                    picking.move_ids.create({
                        'name': line.product_id.display_name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.quantity,
                        'picking_id': picking.id,
                        'location_id': line.location_id.id,
                        'location_dest_id': picking.location_dest_id.id,
                        'sale_line_id': sale_line.id,
                    })
                picking.action_confirm()
                picking.action_assign()
            else:
                loc = self.env['stock.location'].browse(location_id)
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'outgoing'),
                    ('warehouse_id', '=', loc.warehouse_id.id),
                ])
                new_picking = self.env['stock.picking'].create(
                    self.get_stock_picking_data(
                        picking, picking_type, location_id))
                new_picking.group_id = picking.group_id.id
                for line in lines:
                    sale_line = self.picking_id.sale_id.order_line.filtered(
                        lambda ln: ln.product_id == line.product_id)[0]
                    new_picking.move_ids.create(
                        self.get_stock_picking_line_data(
                            line, new_picking, location_id, sale_line))
                new_picking.action_confirm()
                new_picking.action_assign()
                new_pickings.append(new_picking)
        all_locations = self.confirm_line_ids.mapped('location_id')
        for picking in self.picking_id.sale_id.picking_ids:
            if picking.state != 'done' and (
                    picking.location_id not in all_locations):
                picking.action_cancel()
                picking.with_context(is_distribution=True).unlink()
        form_view = self.env.ref('stock.view_picking_form')
        tree_view = self.env.ref('stock.vpicktree')
        search_view = self.env.ref('stock.view_picking_internal_search')
        action_vals = {
            'name': _('Stock pickings'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', [p.id for p in new_pickings])],
        }
        if len(new_pickings) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': new_pickings[0].id,
            })
        return action_vals


class StockDistributionLine(models.TransientModel):
    _name = 'stock.distribution.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.distribution',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    qty_requested = fields.Float(
        string='Quantity requested',
    )
    availability_text = fields.Text(
        string='Availability',
    )


class StockDistributionConfirmLine(models.TransientModel):
    _name = 'stock.distribution.confirm.line'
    _description = 'Wizard confirmation lines'

    @api.model
    def _get_domain_products(self):
        if not self.env.context.get('active_id'):
            return []
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id'))
        product_ids = picking.move_ids.mapped('product_id').ids
        return [('id', 'in', product_ids)]

    @api.model
    def _get_domain_location_stock_wh(self):
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
        ])
        locations = self.env['stock.location']
        for warehouse in warehouses:
            locations_child = self.env['stock.location'].search([
                ('id', 'child_of', warehouse.lot_stock_id.id),
                ('usage', '=', 'internal'),
            ])
            locations |= locations_child
        return [('id', 'in', locations.ids)]

    wizard_id = fields.Many2one(
        comodel_name='stock.distribution',
        string='Wizard',
    )
    picking_id = fields.Many2one(
        related='wizard_id.picking_id',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain=_get_domain_products,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        domain=_get_domain_location_stock_wh,
    )
    quantity = fields.Integer(
        string='Quantity',
    )
