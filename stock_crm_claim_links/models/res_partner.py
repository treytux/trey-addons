# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    claim_ids = fields.One2many(
        comodel_name='crm.claim',
        inverse_name='partner_id',
        string='Claims')
