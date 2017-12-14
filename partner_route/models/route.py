# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class Zone(models.Model):
    _name = 'route.zone'
    _description = 'Route Zone'

    name = fields.Char(
        string='Name',
        required=False)


class RouteSection(models.Model):
    _name = 'route.section'
    _description = 'Route section'

    name = fields.Char(
        string='Name',
        required=True)
    sequence = fields.Integer(
        string='Section')


class Route(models.Model):
    _name = 'route'
    _description = 'Route'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    active = fields.Boolean(
        string='Active',
        default=True)
    name = fields.Char(
        string='Name',
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=_get_company,
        required=True)
    section_id = fields.Many2one(
        string='Section',
        required=True,
        comodel_name='route.section')
    zone_id = fields.Many2one(
        string='Zone',
        required=True,
        comodel_name='route.zone')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman')
    partner_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='route_id',
        string='Partner',
        order='route_sequence')
