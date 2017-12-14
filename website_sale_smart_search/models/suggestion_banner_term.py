# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class SuggestionBannerTerm(models.Model):
    _name = 'suggestion.banner.term'

    name = fields.Char(
        string='Name',
        translate=True)
    banner_id = fields.Many2one(
        comodel_name='suggestion.banner',
        string='Banner')
