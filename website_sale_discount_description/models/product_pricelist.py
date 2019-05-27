###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def get_pricelist_item_all(self, product):
        self.ensure_one()
        date = fields.Date.context_today(self)
        self._cr.execute(
            'SELECT item.id '
            'FROM product_pricelist_item AS item '
            'LEFT JOIN product_category AS categ '
            'ON item.categ_id = categ.id '
            'WHERE (item.product_tmpl_id IS NULL OR item.product_tmpl_id ='
            ' any(%s))'
            'AND (item.product_id IS NULL OR item.product_id = any(%s))'
            'AND (item.categ_id IS NULL OR item.categ_id = any(%s)) '
            'AND (item.pricelist_id = %s) '
            'AND (item.date_start IS NULL OR item.date_start<=%s) '
            'AND (item.date_end IS NULL OR item.date_end>=%s)'
            'ORDER BY item.applied_on, item.min_quantity desc, '
            'categ.parent_left desc', (
                [product.product_tmpl_id.id], [product.id],
                [product.categ_id.id],
                self.id, date, date))
        item_ids = [x[0] for x in self._cr.fetchall()]
        return self.env['product.pricelist.item'].browse(item_ids)
