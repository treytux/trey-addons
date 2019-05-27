# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    display_name = fields.Char(
        compute='compute_display_name')

    @api.one
    @api.depends('comercial')
    def compute_display_name(self):
        res = super(ResPartner, self).name_get()
        if res and res[0] and res[0][0] and res[0][0] == self.id:
            self.display_name = res[0][1]
