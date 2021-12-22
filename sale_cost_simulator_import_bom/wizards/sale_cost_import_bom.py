###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleCostImportBoM(models.TransientModel):
    _name = 'sale.cost.import_bom'
    _description = 'Wizard for import BoM'

    simulator_id = fields.Many2one(
        comodel_name='sale.cost.simulator',
        string='Simulator',
    )
    parent_id = fields.Many2one(
        comodel_name='sale.cost.line',
        string='Parent',
    )
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        required=True,
        string='BoM',
    )
    new_line = fields.Boolean(
        string='New line group',
        default=True,
    )
    line_name = fields.Char(
        string='Line name',
    )

    @api.onchange('bom_id')
    def onchange_bom_id(self):
        self.line_name = self.bom_id.product_id.name

    @api.multi
    def button_accept(self):
        parent = self.parent_id
        if self.new_line:
            parent = self.env['sale.cost.line'].create({
                'product_id': self.bom_id.product_id.id,
                'simulator_id': self.simulator_id.id,
                'pricelist_id': self.simulator_id.pricelist_id.id,
                'parent_id': self.parent_id.id,
                'name': self.line_name,
            })
        for line in self.bom_id.bom_line_ids:
            line = self.env['sale.cost.line'].create({
                'simulator_id': self.simulator_id.id,
                'parent_id': parent.id,
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'quantity': line.product_qty,
                'uom_id': line.product_uom_id.id,
                'pricelist_id': parent.pricelist_id.id,
            })
            line.compute_pricelist()
