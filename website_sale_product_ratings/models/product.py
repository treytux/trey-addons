# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.one
    def _get_rating(self):
        rating_ids = self.env['website_ratings.ratings'].search([
            ('object_model', '=', 'product.template'),
            ('object_id', '=', self.id)], limit=1)
        self.rating_id = rating_ids

    rating_id = fields.Many2one(
        comodel_name='website_ratings.ratings',
        string='Rating',
        compute='_get_rating')
    ratings = fields.Float(
        string='Ratings',
        related='rating_id.ratings')
    numbers_of_ratings = fields.Integer(
        string='Number of Ratings',
        related='rating_id.numbers_of_ratings')
