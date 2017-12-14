# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    analytic_mrp_root_id = fields.Many2one(
        comodel_name='account.analytic.account',
        copy=False,
        string='MRP Root Analytic Account')
