# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_place_ids = fields.One2many(
        comodel_name='product.product.place',
        inverse_name='product_tmpl_id',
        string='Place')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    place_ids = fields.One2many(
        comodel_name='product.product.place',
        inverse_name='product_id',
        string='Place')


class ProductProductPlace(models.Model):
    _name = 'product.product.place'

    name = fields.Char(
        string='Place',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda s: s.env.user.company_id.id)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product')
    location_id = fields.Many2one(
        string='Location',
        domain="[('usage', '=', 'internal')]",
        required=True,
        comodel_name='stock.location')
    note = fields.Text(
        string='Description')

    @api.model
    def _sanitize_vals(self, vals):
        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_tmpl_id'] = product.product_tmpl_id.id
        return vals

    @api.model
    def create(self, vals):
        vals = self._sanitize_vals(vals)
        return super(ProductProductPlace, self).create(vals)

    @api.one
    def write(self, vals):
        vals = self._sanitize_vals(vals)
        return super(ProductProductPlace, self).write(vals)
