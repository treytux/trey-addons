# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api
from dateutil.relativedelta import relativedelta
import logging

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):
        res = super(SaleOrder, self).action_button_confirm()
        _log.info("sales_validate %s", self._ids)
        training_obj = self.env['learning.training']
        subscription_obj = self.env['learning.subscription']
        for order in self:
            for line in order.order_line:
                if line.product_id.product_tmpl_id.subscription_ok:
                    training = training_obj.search([
                        ('template_id',
                         '=', line.product_id.product_tmpl_id.id)])
                    interval = int(training.duration * line.product_uom_qty)
                    date_order = fields.Date.from_string(order.date_order)
                    params = {training.duration_type: interval}
                    date_end = date_order + relativedelta(**params)
                    state = 'draft'
                    if self.payment_acquirer_id:
                        if self.payment_acquirer_id.website_published and \
                                self.payment_acquirer_id.validation:
                            state = 'progress'
                    values = {
                        'state': state,
                        'name': '%s / %s' % (order.partner_id.name,
                                             line.product_id.name_template),
                        'exam_attempts': training.exam_id.exam_attempts,
                        'partner_id': order.partner_id.id,
                        'order_id': order and order[0].id or False,
                        'date_init': date_order,
                        'date_end': date_end,
                        'training_id': training.id,
                    }
                    subscription_obj.create(values)
        return res
