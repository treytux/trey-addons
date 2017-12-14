# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields
import logging

_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contract_type_id = fields.Many2one(
        comodel_name='contract.type',
        string='Contract Type'
    )
