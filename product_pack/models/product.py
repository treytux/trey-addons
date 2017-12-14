# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pack_ids = fields.One2many(
        comodel_name='product.pack',
        inverse_name='product_tmpl_id',
        string='Pack'
    )
    is_pack = fields.Boolean(
        compute='_compute_is_pack',
        string='Is a pack',
        store=True
    )

    @api.one
    @api.depends('pack_ids')
    def _compute_is_pack(self):
        self.is_pack = bool(self.pack_ids)
