# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, exceptions, api, _


class PickingModifyLoc(models.TransientModel):
    _name = 'wiz.picking_modify_loc'

    name = fields.Char(
        string='Name',
    )
    location_src_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location source',
        domain=[('usage', '!=', 'view')],
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location destination',
        domain=[('usage', '!=', 'view')],
    )
    picking_type_code = fields.Char(
        string='Picking type code',
    )

    @api.model
    def default_get(self, fields):
        res = super(PickingModifyLoc, self).default_get(fields)
        active_ids = self.env.context['active_ids']
        if len(active_ids) > 1:
            raise exceptions.Warning(_(
                'This wizard can only be used on a stock picking.'))
        picking = self.env['stock.picking'].browse(active_ids)
        res.update({
            'picking_type_code': picking.picking_type_id.code,
        })
        return res

    @api.multi
    def action_accept(self):
        for wiz in self:
            picking = self.env['stock.picking'].browse(
                self.env.context['active_id'])
            not_allow_states = ['done', 'partially_available', 'assigned']
            if picking.state in not_allow_states:
                raise exceptions.Warning(_(
                    'This wizard can only be applied to stock pickings that '
                    'are not in the \'Done\', \'Partially available\' and '
                    '\'Ready to transfer\' states so as not to interfere with '
                    'stock moves reservations.'))
            for move in picking.move_lines:
                if picking.picking_type_id.code == 'internal':
                    data = {
                        'location_id': wiz.location_src_id.id,
                        'location_dest_id': wiz.location_dest_id.id,
                    }
                elif picking.picking_type_id.code == 'outgoing':
                    data = {
                        'location_id': wiz.location_src_id.id,
                    }
                elif picking.picking_type_id.code == 'incoming':
                    data = {
                        'location_dest_id': wiz.location_dest_id.id,
                    }
                move.write(data)
        return {'type': 'ir.actions.act_window_close'}
