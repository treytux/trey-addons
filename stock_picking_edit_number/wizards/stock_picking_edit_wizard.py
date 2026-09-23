###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPickingEditWizard(models.TransientModel):
    _name = 'stock.picking.edit_wizard'
    _description = 'Force stock picking'

    number = fields.Char(
        string='Picking number',
    )
    date = fields.Date(
        string='Picking date',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id'))
        res.update({
            'number': picking.name,
            'date': (
                picking.scheduled_date
                and fields.Date.to_date(picking.scheduled_date or False)),
        })
        return res

    def button_save(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model != 'stock.picking' or not active_id:
            return {'type': 'ir.actions.act_window_close'}
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id'))
        if picking.name != self.number:
            if self.env['stock.picking'].search([
                ('name', '=', self.number),
            ]):
                raise UserError(_(
                    'There is already a picking with this number.\n'
                    'Please try with another number.'))
            picking.name = self.number
        if fields.Date.to_date(picking.scheduled_date) != self.date:
            picking.scheduled_date = self.date
        return {'type': 'ir.actions.act_window_close'}
