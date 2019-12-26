# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    quality_index = fields.Integer(
        string='Quality index',
        company_dependent=True)
    catalog_code = fields.Char(
        string='Catalog code',
        company_dependent=True)
    trade = fields.Boolean(
        string='Trade')
    dealer = fields.Boolean(
        string='Dealer')
    salesman = fields.Boolean(
        string='Salesman')
    # Por ahora estos campos no se van a tener en cuenta, se usaran los de la
    # campana porque no tenemos historico de precios ni tarifas.
    survey_cost = fields.Float(
        string='Survey cost')
    media_cost = fields.Float(
        string='Media cost')
    activity = fields.Selection(
        selection=[
            ('bar', 'Bar/Coffee'),
            ('restaurant', 'Restaurant/Meson'),
            ('hotel', 'Hotel'),
            ('pub', 'Pub/Disco'),
            ('others', 'Others')],
        string='Activity',
        track_visibility='onchange')
    activity_others = fields.Char(
        string='Others',
        track_visibility='onchange')
    stars = fields.Integer(
        string='Stars',
        track_visibility='onchange')
    survey_collaborator = fields.Boolean(
        string='Survey collaborator')
    name_surveyed = fields.Char(
        string='Name surveyed',
        track_visibility='onchange')
    function_surveyed = fields.Char(
        string='Function surveyed',
        track_visibility='onchange')
    opening_days = fields.Char(
        string='Opening days',
        track_visibility='onchange')
    container_ids = fields.Many2many(
        comodel_name='container',
        relation='partner2container_rel',
        column1='partner_id',
        column2='container_id')
    cube_ids = fields.Many2many(
        comodel_name='cube',
        relation='partner2cube_rel',
        column1='partner_id',
        column2='cube_id')
