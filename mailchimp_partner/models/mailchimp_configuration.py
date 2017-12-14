# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class MailchimpConfig(models.Model):
    _inherit = 'mailchimp.config'

    customers = fields.Boolean(
        string='Customers'
    )
    customer_contacts = fields.Boolean(
        string='Customer contacts'
    )
    suppliers = fields.Boolean(
        string='Suppliers'
    )
    supplier_contacts = fields.Boolean(
        string='Supplier contacts'
    )
