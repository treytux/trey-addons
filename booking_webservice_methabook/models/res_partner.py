# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import datetime
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_account_ref_methabook = fields.Char(
        string='Customer Account Ref',
        help='Customer Account reference number from methabook platform',
        required=False)
    supplier_account_ref_methabook = fields.Char(
        string='Supplier Account Ref',
        help='Supplier Account reference number from methabook platform',
        required=False)
    processed_ok = fields.Boolean(
        string='Processed',
        help='Processed correctly in Methabook')
    credit_limit_reached = fields.Boolean(
        string='No credit')
    credit_limit_reached_date = fields.Date(
        string="Date",
        default=datetime.date.today() - datetime.timedelta(days=7))
