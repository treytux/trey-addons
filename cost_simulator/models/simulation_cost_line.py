# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class SimulationCostLine(models.Model):
    _name = 'simulation.cost.line'
    _description = 'Simulation Cost Line'
    _order = 'id'

    sequence = fields.Integer(
        string='Sequence',
        required=False)
    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade')
    chapter_tmpl_id = fields.Many2one(
        comodel_name='simulation.cost.chapter.template',
        string='Chapter template',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Text(
        string='Description')
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier')
    cost_price = fields.Float(
        string='Cost Price',
        default=0)
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='UoM',
        digits_compute=dp.get_precision('Product UoM'),
        required=True)
    uom_qty = fields.Float(
        string='Quantity',
        digits_compute=dp.get_precision('Product UoS'),
        default=1)
    subtotal_cost = fields.Float(
        string='Subtotal Cost',
        compute='calculate_subtotals',
        readonly=True)

    @api.onchange('product_id', 'uom_id', 'uom_qty', 'cost_price')
    def calculate_subtotals(self):
        self.subtotal_cost = self.cost_price * self.uom_qty

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {}
        self.supplier_id = self.product_id.product_tmpl_id.seller_id or False
        self.cost_price = self.product_id.product_tmpl_id.standard_price
        self.name = self.product_id.name_template
        self.uom_id = self.product_id.uom_id.id

    @api.one
    def update_cost(self):
        self.product_id_change()
