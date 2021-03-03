###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _select_seller(
            self, partner_id=False, quantity=0.0, date=None, uom_id=False,
            params=False):
        res = super()._select_seller(
            partner_id=partner_id, quantity=quantity, date=date, uom_id=uom_id,
            params=params)
        if quantity >= 0:
            return res
        sellers = self._prepare_sellers(params)
        if self.env.context.get('force_company'):
            sellers = sellers.filtered(
                lambda s:
                    not s.company_id
                    or s.company_id.id == self.env.context['force_company']
            )
        for seller in sellers:
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(
                    quantity_uom_seller, seller.product_uom)
            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [
                    partner_id, partner_id.parent_id]:
                continue
            if seller.product_id and seller.product_id != self:
                continue
            res |= seller
            break
        return res
