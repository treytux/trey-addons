# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    discount_type = fields.Selection(
        selection=[
            ('none', 'Without discount'),
            ('percent_total', 'Total discount percent'),
            ('quantity_total', 'Total discount quantity')],
        string='Discount type',
        default='none',
        required=True)
    discount_applied = fields.Float(
        string='Discount applied (%)',
        digits_compute=dp.get_precision('Sale price'))
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Discount product')
    discount_quantity = fields.Float(
        string='Discount quantity')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            if not self.product_id.taxes_id:
                raise exceptions.Warning(
                    _('Please define a product tax in product template.'))
            if self.product_id.type != 'service':
                raise exceptions.Warning(
                    _('Please, product type must be service.'))
            if not self.product_id.categ_id:
                raise exceptions.Warning(
                    _('Please, define a product categ.'))

    @api.onchange('discount_type')
    def onchange_discount_type(self):
        if self.discount_type == 'none':
            self.product_id = None
            self.discount_applied = 0.
            self.discount_quantity = 0.
