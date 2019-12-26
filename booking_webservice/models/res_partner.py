# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    code_ids = fields.One2many(
        comodel_name='booking.webservice.partner.ref',
        inverse_name='partner_id',
        string="Juniper Ids",
        required=False)
    customer_account_ref = fields.Char(
        string='Customer Account Ref',
        help='Customer Account reference number from juniper platform',
        required=False)
    supplier_account_ref = fields.Char(
        string='Supplier Account Ref',
        help='Supplier Account reference number from juniper platform',
        required=False)
