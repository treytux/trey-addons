# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    subvention_percent = fields.Float(
        string='Subvention (%)',
        track_visibility='onchange')
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention',
        track_visibility='onchange')
