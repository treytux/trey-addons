# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rating = fields.Float(
        string='Product Rating',
        digits=(2, 1),
        compute="_get_product_rating")
    rating_count = fields.Integer(
        string="Nº comments",
        compute="_comments_count")

    @api.one
    def _comments_count(self):
        self.rating_count = len([
            x.id for x in self.website_message_ids
            if (x.message_rate > 0 and x.website_published)])

    @api.one
    def _get_product_rating(self):
        messages = [x for x in self.website_message_ids
                    if (x.message_rate > 0 and x.website_published)]
        if messages:
            total_rating = sum([m.message_rate for m in messages])
            self.rating = total_rating * 1. / len(messages)

    @api.multi
    def message_post(self, **kwargs):
        message_id = super(ProductTemplate, self).message_post(**kwargs)
        ratings_rate = self.env.context.get('comment_ratings_rate')
        if all([ratings_rate,
                self.env.context.get('comment_ratings_rate', '0') != '0']):
            comment_ids = self.env['mail.message'].search([
                ('model', '=', 'product.template'),
                ('res_id', '=', self.id),
                ('type', '=', 'comment'),
                ('create_uid', '=', self.env.uid),
                ('message_rate', '!=', 0)])
            if not comment_ids:
                mail_message = self.env['mail.message'].browse(message_id)
                mail_message.message_rate = ratings_rate
        return message_id
