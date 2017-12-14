# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models, fields
import logging
_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    root_partner_id = fields.Many2one(
        comodel_name='res.partner',
        compute='_compute_root_partner_id',
        store=True,
        string='Root partner')

    @api.one
    @api.depends('parent_id')
    def _compute_root_partner_id(self):
        if self.is_company:
            self.root_partner_id = self.id
        else:
            partner = self
            if partner.parent_id:
                while partner.parent_id:
                    partner = partner.parent_id
                    if partner.is_company:
                        self.root_partner_id = partner.id
            else:
                self.root_partner_id = partner.id
