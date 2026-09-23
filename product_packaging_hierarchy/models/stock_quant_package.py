###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    parent_id = fields.Many2one(
        comodel_name='stock.quant.package',
        string='Parent package',
        ondelete='cascade',
    )
    child_ids = fields.One2many(
        comodel_name='stock.quant.package',
        inverse_name='parent_id',
        string='Child packages',
    )
    child_quant_ids = fields.Many2many(
        comodel_name='stock.quant',
        compute='_compute_child_quant_ids',
        help='Shows the content (quants) of the current package childs.',
    )
    has_child_ids = fields.Boolean(
        string='Has child packages',
        compute='_compute_child_quant_ids',
    )

    @api.depends('child_ids', 'child_ids.quant_ids')
    def _compute_child_quant_ids(self):
        for package in self:
            quant_ids = package.child_ids.mapped('quant_ids').ids
            package.child_quant_ids = [(6, 0, quant_ids)]
            package.has_child_ids = bool(package.child_ids)
