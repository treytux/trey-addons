# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SuggestionBanner(models.Model):
    _name = 'suggestion.banner'

    name = fields.Char(
        string='Name',
        translate=True)
    image = fields.Binary(
        string='Image',
        help='Recomended 728x90 pixels size in .png, .jpg or .gif formats.')
    term_ids = fields.One2many(
        comodel_name='suggestion.banner.term',
        inverse_name='banner_id',
        string='Terms',
        help='The banner will be shown when one of this terms appears on '
             'search query.')
    default = fields.Boolean(
        string='Default',
        help='Will be displayed by default if no other banner is shown.')
    href = fields.Char(
        string='Link',
        help='Where to go when user clicks on the banner.')


class SuggestionBannerTerm(models.Model):
    _name = 'suggestion.banner.term'

    name = fields.Char(
        string='Name',
        translate=True)
    banner_id = fields.Many2one(
        comodel_name='suggestion.banner',
        string='Banner')
