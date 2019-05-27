# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, exceptions, api, _


class PickingModifyLoc(models.TransientModel):
    _name = 'wiz.picking_modify_loc'

    name = fields.Char(
        string='Name')
    picking_type = fields.Selection(
        selection=[
            ('incoming', 'Incoming'),
            ('outgoing', 'Outgoing'),
            ('internal', 'Internal')],
        string='Picking Type')
    location_orig_in_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location origin')
    location_dest_in_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location destination')
    location_orig_out_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location origin')
    location_dest_out_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location destination')

    @api.model
    def default_get(self, fields):
        res = super(PickingModifyLoc, self).default_get(fields)
        if self.env.context.get('active_id', False):
            picking = self.env['stock.picking'].browse(
                self.env.context['active_id'])
            res.update({'picking_type': picking.picking_type_id.code})
            if picking.picking_type_id.code == 'internal':
                return res
            location_src_id = (
                picking.picking_type_id.default_location_src_id and
                picking.picking_type_id.default_location_src_id.id or None)
            location_dest_id = (
                picking.picking_type_id.default_location_dest_id.id)
            if picking.picking_type_id.code == 'incoming':
                res.update({
                    'location_orig_in_id': location_src_id,
                    'location_dest_in_id': location_dest_id})
            else:
                res.update({
                    'location_orig_out_id': location_src_id,
                    'location_dest_out_id': location_dest_id})
        return res

    @api.multi
    def action_accept(self):
        message = _(
            'This wizard only works incoming or outgoing pickings whose stock '
            'moves is not being in the \'Done\' state.')
        for wiz in self:
            picking = self.env['stock.picking'].browse(
                self.env.context['active_id'])
            if picking.picking_type_id.code not in ['outgoing', 'incoming']:
                raise exceptions.Warning(message)
            for move in picking.move_lines:
                if move.state == 'done':
                    raise exceptions.Warning(message)
                move.write(
                    {'location_id': wiz.location_orig_out_id.id
                     if picking.picking_type_id.code == 'outgoing'
                     else wiz.location_orig_in_id.id,
                     'location_dest_id': wiz.location_dest_out_id.id
                     if picking.picking_type_id.code == 'outgoing'
                     else wiz.location_dest_in_id.id})
        return {'type': 'ir.actions.act_window_close'}
