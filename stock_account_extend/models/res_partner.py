# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    picking2invoice_ids = fields.One2many(
        comodel_name='stock.picking',
        compute='_compute_picking2invoice',
        string='Picking to invoice')
    picking2invoice_count = fields.Integer(
        compute='_compute_picking2invoice',
        string='Picking count')

    @api.one
    def _compute_picking2invoice(self):
        pickings = self.env['stock.picking'].search([
            ('partner_id', '=', self.id),
            ('state', '=', 'done'),
            ('invoice_state', '=', '2binvoiced'),
            ('company_id', '=', self.env.user.company_id.id)])
        self.picking2invoice_ids = pickings
        self.picking2invoice_count = len(pickings)

    @api.multi
    def picking2invoice_tree_view(self):
        context = {
            'default_res_model': self._name,
            'default_res_id': self.id,
            'default_partner_id': self.id,
            'search_default_partner_id': self.id,
        }
        return {
            'name': _('Pickings to Invoice'),
            'domain': [('id', 'in', self.picking2invoice_ids.ids)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': context.__str__()}
