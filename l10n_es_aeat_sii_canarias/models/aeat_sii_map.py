# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AeatSiiMap(models.Model):
    _inherit = 'aeat.sii.map'

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State')
