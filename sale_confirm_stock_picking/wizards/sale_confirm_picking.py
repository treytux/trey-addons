# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, api, exceptions, fields, models


class WizSaleConfirmPicking(models.TransientModel):
    _name = 'wiz.sale.confirm.picking'
    _description = 'Confirm Picking From Sale'

    number = fields.Char(
        string='Picking Number',
    )
    date = fields.Date(
        string='Picking Date',
    )

    @api.multi
    def button_confirm(self):
        sale_obj = self.env['sale.order']
        picking_obj = self.env['stock.picking']
        active_ids = self.env.context.get('active_ids', [])
        for sale in sale_obj.browse(active_ids):
            if not any(sale.mapped('order_line.product_id').filtered(
                    lambda p: p.type in ['product', 'consu'])):
                raise exceptions.Warning(
                    _('This quotation only have product services.\n Please '
                      'use Confirm Sale button.'))
            if any(sale.mapped('order_line.product_id').filtered(
                    lambda p: p.track_all or p.track_outgoing)):
                raise exceptions.Warning(
                    _('At least one product has lot tracking.\n Please '
                      'uncheck to confirm sale and transfer picking '
                      'yourself.'))
            if picking_obj.search([('name', '=', self.number)]):
                raise exceptions.Warning(
                    _('There is already a picking with this number.\n Please '
                      'try with another number.'))
            if sale.action_button_confirm():
                picking = sale.picking_ids[:1]
                if picking:
                    picking.name = self.number
                    if picking.state in \
                            ['confirmed', 'waiting', 'partially_available']:
                        picking.force_assign()
                    else:
                        picking.do_transfer()
                    picking.action_done()
                    picking.date = self.date
                    picking.min_date = self.date
                    picking.date_done = self.date
        return {'type': 'ir.actions.act_window_close'}
