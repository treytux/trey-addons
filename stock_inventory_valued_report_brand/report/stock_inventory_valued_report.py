###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockInventoryValuedReport(models.Model):
    _inherit = 'stock.inventory_valued.report'

    product_brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
    )

    def _select(self):
        select_lst = super()._select()
        select_lst.append('t.product_brand_id as product_brand_id')
        return select_lst

    def _group_by(self):
        group_by_lst = super()._group_by()
        group_by_lst.append('t.product_brand_id')
        return group_by_lst
