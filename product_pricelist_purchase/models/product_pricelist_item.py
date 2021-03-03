###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    purchase_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist.purchase',
        string='Purchase pricelist',
    )
    base = fields.Selection(
        selection_add=[
            ('purchase_price', 'Purchase price reference'),
        ],
    )

    def _check_base(self, base, is_sale):
        if is_sale and base == 'purchase_price':
            raise UserError(
                _('Don\'t use purchase price reference in sale pricelist'))
        return True

    @api.model
    def create(self, vals):
        self._check_base(vals.get('base'), bool(vals.get('pricelist_id')))
        return super().create(vals)

    @api.multi
    def write(self, vals):
        re = super().write(vals)
        for item in self:
            self._check_base(item.base, bool(item.pricelist_id))
        return re
