# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    app_published = fields.Boolean(
        string='App published',
        default=True)
