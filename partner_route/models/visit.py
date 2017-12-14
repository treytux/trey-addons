# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class Visit(models.Model):
    _name = 'partner.visit'
    _description = 'Partner visit from routes'
    _order = 'date DESC'

    name = fields.Char(
        string='Name')
    route_id = fields.Many2one(
        comodel_name='route',
        string='Route',
        required=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman',
        required=True)
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True)
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order')
    stock_ids = fields.One2many(
        comodel_name='partner.visit.stock',
        inverse_name='visit_id',
        string='Stock')
    notes = fields.Text('Notes')

    @api.one
    def name_get(self):
        return (self.id, '%s (%s), %s' % (
            self.partner_id.name, self.route_id.name, self.user_id.name))


class VisitStock(models.Model):
    _name = 'partner.visit.stock'
    _description = 'Partner visit Stock'

    visit_id = fields.Many2one(
        comodel_name='partner.visit',
        string='Visit')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Default Unit Of Measure')
