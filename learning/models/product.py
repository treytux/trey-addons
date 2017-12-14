# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields
import logging

_log = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    subscription_ok = fields.Boolean(
        string='Subscription',
        help="Specify if the product can be selected for subscriptions."
    )
    training_ids = fields.One2many(
        comodel_name="learning.training",
        inverse_name="template_id",
        string="Training",
        required=False
    )
