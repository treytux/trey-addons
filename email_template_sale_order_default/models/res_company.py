# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_sale_order_email_template = fields.Many2one(
        comodel_name='email.template',
        string='Default sale order email template',
        domain='[("model_id.model", "=", "sale.order")]')
