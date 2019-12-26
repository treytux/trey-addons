# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default supplier',
        domain=[('supplier', '=', 'True')],
        required=True)
