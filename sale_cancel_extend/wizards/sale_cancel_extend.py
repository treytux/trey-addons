# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _
import logging

_log = logging.getLogger(__name__)


class SaleCancel(models.TransientModel):
    _name = 'wiz.sale.cancel'
    _description = 'Cancel sale orders selected'

    name = fields.Char(string='Empty')
    reason = fields.Text(
        string='Reason',
        required=True,
        translate=True)

    @api.multi
    def button_cancel(self):
        '''Cancel orders and write the reason in the wall.'''
        orders = self.env['sale.order'].browse(
            self.env.context.get('active_ids', []))
        for order in orders:
            order.action_cancel()
            order.with_context(mail_post_autofollow=False).message_post(
                subject=_('Order canceled'),
                body=_('Reason: %s' % self.reason))
        return {'type': 'ir.actions.act_window_close'}
