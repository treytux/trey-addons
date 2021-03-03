###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    margin = fields.Float(
        string='Margin (%)',
        digits=dp.get_precision('Discount'),
    )
    list_price = fields.Float(
        compute='_compute_list_price',
        store=True,
        readonly=False,
    )

    @api.onchange('standard_price', 'margin')
    def _compute_list_price(self):
        for template in self:
            if not template.standard_price:
                continue
            if template.margin >= 100:
                template.margin = 99.99
            margin = template.margin and (template.margin / 100) or 0
            template.list_price = template.standard_price / (1 - margin)

    @api.onchange('list_price')
    def onchange_list_price(self):
        if not self.standard_price or not self.list_price:
            self.margin = 0
            return
        margin = self.standard_price / self.list_price
        margin = (margin - 1) * -100
        self.margin = margin >= 100 and 99.99 or margin
