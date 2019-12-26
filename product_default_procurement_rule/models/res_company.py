# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields
import openerp.addons.decimal_precision as dp


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse')
    default_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location')
    default_product_min_qty = fields.Float(
        string='Minimum Quantity',
        default=0,
        digits_compute=dp.get_precision('Product Unit of Measure'))
    default_product_max_qty = fields.Float(
        string='Maximum Quantity',
        default=0,
        digits_compute=dp.get_precision('Product Unit of Measure'))
    default_qty_multiple = fields.Float(
        string='Qty Multiple',
        default=1,
        digits_compute=dp.get_precision('Product Unit of Measure'))
    is_reordering_default = fields.Boolean(
        string='Active Default Reordering Rule')
