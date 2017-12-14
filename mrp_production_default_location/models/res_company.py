# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    mrp_location_src_id = fields.Many2one(
        comodel_name='stock.location',
        string='Mrp raw materials location',
        help='Raw material location to assign in production orders. If it is '
        'empty, will use default stock location.')
    mrp_location_dst_id = fields.Many2one(
        comodel_name='stock.location',
        string='Mrp finished Products Location',
        help='Finished products location to assign in production orders. If '
        'it is empty, will use default stock location.')
