# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.


from openerp import models, fields, _


class Country(models.Model):
    _inherit = 'res.country'

    website_published = fields.Boolean(
        string=_('Visible in Portal / Website'),
        default=True)
