# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class WizCreateRoute(models.TransientModel):
    _name = 'wiz.create_route'

    name = fields.Char(
        string='Empty')
    user_salesman_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman',
        required=True)
    zone_id = fields.Many2one(
        comodel_name='route.zone',
        string='Zone',
        required=True)
    section_ids = fields.Many2many(
        comodel_name='route.section',
        relation='wiz_create_route2route_section_rel',
        column1='wiz_create_route_id',
        column2='route_section_id',
        required=True)

    @api.multi
    def button_accept(self):
        '''Create routes for a salesman for the zone and selected sections.'''
        route_ids = []
        routes = []
        for section in self.section_ids:
            data = {
                'name': '%s, %s' % (self.zone_id.name, section.name),
                'company_id': self.user_salesman_id.company_id.id,
                'section_id': section.id,
                'zone_id': self.zone_id.id,
                'user_id': self.user_salesman_id.id}
            route = self.env['route'].create(data)
            route_ids.append(route.id)
            routes.append(route)
        # Show routes created for this salesman
        form_view = self.env.ref('partner_route.form_route')
        tree_view = self.env.ref('partner_route.tree_route')
        search_view = self.env.ref('partner_route.search_route')
        return {
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'route',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'search_view_id': search_view.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', route_ids)],
            'context': self.env.context}
