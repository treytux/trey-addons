# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    block_when_unpaid = fields.Boolean(
        string='Block when unpaid',
        default=True)

    @api.multi
    def get_unpaid_partner(self):
        return [partner for partner in self.env['res.partner'].search(
                [('block_when_unpaid', '=', True)])
                if partner.credit_total < 0]
