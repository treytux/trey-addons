###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='BoM for compute manufacture stock',
        domain='[("product_tmpl_id", "=", product_tmpl_id)]',
    )
    qty_manufacture = fields.Float(
        string='Manufacture',
        compute='_compute_quantities',
        digits=dp.get_precision('Product Unit of Measure'),
        help='Quantity of stock compute from BoM.',
    )

    def _compute_quantities_dict(self, lot_id, owner_id, package_id,
                                 from_date=False, to_date=False):
        res = super()._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date=from_date, to_date=to_date)
        for product in self:
            res[product.id]['qty_manufacture'] = (
                product.qty_bom_available_get()
            )
        return res

    def qty_bom_available_get(self):
        self.ensure_one()
        bom = self.stock_bom_id
        if self._context.get('bom_id'):
            context_bom = self.stock_bom_id.browse(self._context.get('bom_id'))
            if context_bom.product_id == self:
                bom = context_bom
        if not bom:
            return 0
        return int(min([
            ln.product_id.qty_available / ln.product_qty
            for ln in bom.bom_line_ids]) * bom.product_qty)

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    def _compute_quantities(self):
        super()._compute_quantities()
        for product in self:
            product.qty_manufacture = product.qty_bom_available_get()
            if self._context.get('qty_manufacture_add_to_virtual'):
                product.virtual_available += product.qty_manufacture

    def action_report_mrp_bom(self):
        self.ensure_one()
        action = self.env.ref('mrp.action_report_mrp_bom')
        res = action.read()[0]
        res.update({
            'res_id': self.stock_bom_id.id,
            'context': {
                'active_model': 'mrp.bom',
                'active_id': self.stock_bom_id.id,
                'active_ids': [self.stock_bom_id],
            },
        })
        return res
