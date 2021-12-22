###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SimulationCostLine(models.Model):
    _name = 'simulation.cost.line'
    _description = 'Simulation Cost Line'
    _order = 'id'

    sequence = fields.Integer(
        string='Sequence',
    )
    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade',
    )
    chapter_tmpl_id = fields.Many2one(
        comodel_name='simulation.cost.chapter.template',
        string='Chapter template',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
    )
    cost_price = fields.Float(
        string='Cost Price',
        default=0,
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM',
        digits=dp.get_precision('Product UoM'),
        required=True,
    )
    uom_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product UoS'),
        default=1,
    )
    subtotal_cost = fields.Float(
        string='Subtotal Cost',
        compute='_compute_subtotals',
        readonly=True,
    )

    @api.depends('product_id', 'uom_id', 'uom_qty', 'cost_price')
    def _compute_subtotals(self):
        for line in self:
            line.subtotal_cost = line.cost_price * line.uom_qty

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {}
        seller = self.product_id.product_tmpl_id.seller_ids[:1]
        if seller:
            self.supplier_id = seller.id
        self.cost_price = self.product_id.product_tmpl_id.standard_price
        self.name = self.product_id.product_tmpl_id.name
        self.uom_id = self.product_id.uom_id.id

    @api.one
    def update_cost(self):
        self.product_id_change()
