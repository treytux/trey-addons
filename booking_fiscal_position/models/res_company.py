# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_fp_intra = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Sale Intra-Comunity',
        required=False)
    sale_fp_extra = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Sale Extra-Community',
        required=False)
    purchase_fp_intra = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Purchase Intra-Community',
        required=False)
    purchase_fp_extra = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Purchase Extra-Community',
        required=False)
    commission_fp_intra = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Commission Intra-Community',
        required=False)
    commission_fp_extra = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Commission Extra-Community',
        required=False)
