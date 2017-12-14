# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields
from openerp.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    length = fields.Float(
        digits=dp.get_precision('Product UoS'))
    height = fields.Float(
        digits=dp.get_precision('Product UoS'))
    width = fields.Float(
        digits=dp.get_precision('Product UoS'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    length = fields.Float(
        digits=dp.get_precision('Product UoS'))
    height = fields.Float(
        digits=dp.get_precision('Product UoS'))
    width = fields.Float(
        digits=dp.get_precision('Product UoS'))
