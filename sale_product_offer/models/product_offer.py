# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class ProductOffer(models.Model):
    _name = 'product.offer'
    _description = 'Product Offer'
    _order = 'date_start desc, date_end desc'

    name = fields.Char(
        string='Offer',
        required=True,
    )
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        domain=[('customer', '=', True)],
        index=True,
    )
    date_start = fields.Date(
        string='Start Date',
        index=True,
        required=True,
        help='Starting date for the offer item validation'
    )
    date_end = fields.Date(
        string='End Date',
        index=True,
        required=True,
        help='Ending date for the offer item validation'
    )
    line_ids = fields.One2many(
        comodel_name='product.offer.line',
        inverse_name='offer_id',
        string='Lines',
        copy=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )

    @api.multi
    def get_product_offer(self, customer_id=None, product_id=None):
        date_now = fields.Date.context_today(self)
        if not product_id and not customer_id:
            return False
        lines = self.env['product.offer.line'].search([
            ('date_start', '<=', date_now), ('date_end', '>=', date_now),
            ('product_id', '=', product_id),
            ('customer_id', '=', customer_id)])
        if lines:
            return lines
        lines = self.env['product.offer.line'].search([
            ('date_start', '<=', date_now), ('date_end', '>=', date_now),
            ('product_id', '=', product_id)])
        if lines:
            return lines
        return False
