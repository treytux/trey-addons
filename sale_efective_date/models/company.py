# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    default_sale_order_validity_days = fields.Integer(
        string="")

    _sql_constraints = [
        ('sale_order_validity_days_positive',
         'CHECK (default_sale_order_validity_days >= 0)',
         "The value of the field 'Default Validity Duration of Sale Orders' "
         "must be positive or 0."),
    ]
