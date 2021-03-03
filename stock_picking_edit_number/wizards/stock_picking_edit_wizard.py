# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, api, exceptions, fields, models


class StockPickingEditWizard(models.TransientModel):
    _name = 'stock.picking.edit_wizard'
    _description = 'Force Stock Picking'

    number = fields.Char(
        string='Picking Number',
    )
    date = fields.Date(
        string='Picking Date',
    )

    @api.model
    def default_get(self, fields):
        res = super(StockPickingEditWizard, self).default_get(fields)
        picking = self.env['stock.picking'].browse(self._context['active_id'])
        res.update({
            'number': picking.name,
            'date': picking.date,
        })
        return res

    @api.multi
    def button_save(self):
        picking_obj = self.env['stock.picking']
        for picking in picking_obj.browse(self._context['active_id']):
            if picking.name != self.number:
                if picking_obj.search([('name', '=', self.number)]):
                    raise exceptions.Warning(
                        _('There is already a picking with this number.\n '
                          'Please try with another number.'))
                picking.name = self.number
            if picking.date != self.date:
                picking.date = self.date
                picking.min_date = self.date
                picking.date_done = self.date
        return {'type': 'ir.actions.act_window_close'}
