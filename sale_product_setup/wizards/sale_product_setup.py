###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleProductSetup(models.TransientModel):
    _name = 'sale.product_setup'
    _description = 'Product setup'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        domain='[("is_setup", "=", False)]',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='sale.product_setup_line',
        inverse_name='setup_id',
        string='Lines',
    )

    def create_lines(self):
        self.line_ids.unlink()
        if not self.product_tmpl_id:
            return
        line_obj = self.env['sale.product_setup_line']
        for setup in self.product_tmpl_id.setup_ids:
            line_obj.create({
                'wizard_id': self.id,
                'setup_id': self.id,
                'name': setup.name,
                'categ_id': setup.categ_id.id,
            })


class SaleProductSetupLine(models.TransientModel):
    _name = 'sale.product_setup_line'
    _description = 'Product setup line'
    _order = 'sequence'

    wizard_id = fields.Many2one(
        comodel_name='sale.product_setup',
        string='Wizard',
        required=True,
    )
    setup_id = fields.Many2one(
        comodel_name='sale.product_setup',
        string='Setup',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    categ_id = fields.Many2one(
        comodel_name='product.setup.category',
        string='Category',
        required=True,
    )
    required = fields.Boolean(
        string='Required',
    )
    quantity = fields.Float(
        string='Quantity',
        default=1,
    )

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        for line in self:
            if line.name:
                continue
            if not line.categ_id:
                continue
            line.name = line.categ_id.name
