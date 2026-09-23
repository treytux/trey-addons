###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    picking_quantity = fields.Selection(
        selection_add=[
            ('one', 'One label for each product'),
            ('line', 'One label for each line'),
            ('total', 'Total product quantity'),
            ('select_moves', 'Select Operations to print'),
            ('select_move_lines', 'Select Moves to print'),
        ],
        ondelete={
            'one': 'set default',
            'line': 'set default',
            'total': 'set default',
            'select_moves': 'set default',
            'select_move_lines': 'set default',
        },
        default='total',
    )
    select_move_ids = fields.One2many(
        comodel_name='product.label.layout.move',
        inverse_name='layout_id',
        string='Operations',
    )
    select_move_line_ids = fields.One2many(
        comodel_name='product.label.layout.move.line',
        inverse_name='layout_id',
        string='Moves',
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        picking_quantity = values.get('picking_quantity')
        if picking_quantity not in ('select_moves', 'select_move_lines'):
            return values
        move_line_ids = self.env.context.get('default_move_line_ids', [])
        move_lines = self.env['stock.move.line'].browse(move_line_ids)
        if picking_quantity == 'select_moves':
            values['select_move_ids'] = [
                (0, 0, {
                    'move_line_id': move_line.id,
                    'quantity': int(move_line.qty_done),
                })
                for move_line in move_lines
            ]
        else:
            values['select_move_line_ids'] = [
                (0, 0, {
                    'move_id': move.id,
                    'quantity': int(move.product_uom_qty),
                })
                for move in move_lines.mapped('move_id')
            ]
        return values

    @api.onchange('picking_quantity')
    def _onchange_picking_quantity(self):
        self.select_move_ids = [(5, 0, 0)]
        self.select_move_line_ids = [(5, 0, 0)]
        if self.picking_quantity == 'select_moves':
            self.select_move_ids = [
                (0, 0, {
                    'move_line_id': move_line.id,
                    'quantity': int(move_line.qty_done),
                })
                for move_line in self.move_line_ids
            ]
        elif self.picking_quantity == 'select_move_lines':
            self.select_move_line_ids = [
                (0, 0, {
                    'move_id': move.id,
                    'quantity': int(move.product_uom_qty),
                })
                for move in self.move_line_ids.mapped('move_id')
            ]

    def _prepare_report_data(self):
        self.ensure_one()
        xml_id, data = super()._prepare_report_data()
        if self.picking_quantity not in (
                'one', 'line', 'total', 'select_moves', 'select_move_lines'):
            return xml_id, data
        if self.picking_quantity == 'one':
            products = (
                self.move_line_ids.mapped('product_id') or self.product_ids
            )
            data['quantity_by_product'] = {
                product.id: 1
                for product in products
            }
        elif self.picking_quantity == 'line':
            quantities = {}
            for move_line in self.move_line_ids:
                product_id = move_line.product_id.id
                quantities[product_id] = quantities.get(product_id, 0) + 1
            if not quantities:
                raise UserError(_('There are no picking lines to print.'))
            data['quantity_by_product'] = quantities
        elif self.picking_quantity == 'total':
            quantities = {}
            for move_line in self.move_line_ids:
                quantity = int(move_line.qty_done)
                if quantity <= 0:
                    continue
                product_id = move_line.product_id.id
                quantities[product_id] = (
                    quantities.get(product_id, 0) + quantity
                )
            if not quantities:
                raise UserError(_('There are no products to print.'))
            data['quantity_by_product'] = quantities
        elif self.picking_quantity == 'select_moves':
            quantities = {}
            for operation_line in self.select_move_ids:
                quantity = operation_line.quantity
                if quantity <= 0:
                    continue
                product_id = operation_line.move_line_id.product_id.id
                quantities[product_id] = (
                    quantities.get(product_id, 0) + quantity
                )
            if not quantities:
                raise UserError(_('There are no operations to print.'))
            data['quantity_by_product'] = quantities
        else:
            quantities = {}
            for move_line in self.select_move_line_ids:
                quantity = move_line.quantity
                if quantity <= 0:
                    continue
                product_id = move_line.move_id.product_id.id
                quantities[product_id] = (
                    quantities.get(product_id, 0) + quantity
                )
            if not quantities:
                raise UserError(_('There are no moves to print.'))
            data['quantity_by_product'] = quantities
        return xml_id, data


class ProductLabelLayoutMove(models.TransientModel):
    _name = 'product.label.layout.move'
    _description = 'Product label layout move'

    layout_id = fields.Many2one(
        comodel_name='product.label.layout',
        required=True,
        ondelete='cascade',
    )
    move_line_id = fields.Many2one(
        comodel_name='stock.move.line',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        related='move_line_id.product_id',
        readonly=True,
    )
    quantity = fields.Integer(
        string='Quantity',
        readonly=True,
    )


class ProductLabelLayoutMoveLine(models.TransientModel):
    _name = 'product.label.layout.move.line'
    _description = 'Product label layout move line'

    layout_id = fields.Many2one(
        comodel_name='product.label.layout',
        required=True,
        ondelete='cascade',
    )
    move_id = fields.Many2one(
        comodel_name='stock.move',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        related='move_id.product_id',
        readonly=True,
    )
    quantity = fields.Integer(
        string='Quantity',
        readonly=True,
    )
