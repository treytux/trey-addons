# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, fields
import datetime
import logging

_log = logging.getLogger(__name__)


class WarningMessaging(models.Model):
    _inherit = 'warning.messaging'

    @api.one
    def do_send_msg(self, objs, action):
        if self.model_id.name == 'crm.lead':
            for crm_lead in objs:
                partner_ids = [
                    crm_lead.user_id and crm_lead.user_id.partner_id and
                    crm_lead.user_id.partner_id.id] or []
                crm_lead.with_context(mail_post_autofollow=False).message_post(
                    body=self.body, partner_ids=partner_ids)
            return True
        else:
            return super(WarningMessaging, self).do_send_msg(objs, action)

    @api.one
    def do_create_call(self, objs, action):
        if self.model_id.name == 'sale.order':
            for sale_order in objs:
                self.env['crm.phonecall'].create({
                    'name': (
                        '[AVISO] Llamada generada desde presupuesto \'%s\'' % (
                            sale_order.name)),
                    'partner_id': (sale_order.partner_id and
                                   sale_order.partner_id.id or None),
                    'user_id': (sale_order.user_id and
                                sale_order.user_id.id or None),
                })
        return True

    @api.one
    def do_create_meeting(self, objs, action):
        if self.model_id.name == 'sale.order':
            for sale_order in objs:
                # @TODO Para cuando hay que planificar la reunion?
                # Por ahora, al dia siguiente y duracion=1hora. Luego,
                # poner configurable en la accion
                format_date = '%Y-%m-%d %H:%M:%S'
                start = (
                    datetime.datetime.now() +
                    datetime.timedelta(days=1)).strftime(format_date)
                stop = (
                    datetime.datetime.now() +
                    datetime.timedelta(days=1, hours=1)).strftime(format_date)

                self.env['calendar.event'].create({
                    'name': '[AVISO] Reunion generada desde presupuesto \'%s\''
                    % (sale_order.name),
                    'start': start,
                    'stop': stop,
                    'user_id': sale_order.user_id and sale_order.user_id.id or
                    None,
                    # 'description': , # Reunion con el cliente...
                })

        return True

    @api.one
    def do_create_opportunity(self, objs, action):
        if self.model_id.name == 'sale.order':
            for sale_order in objs:
                self.env['crm.lead'].create({
                    'name': '[AVISO] Oportunidad generada desde presupuesto '
                    '\'%s\'' % (sale_order.name),
                    'partner_id': sale_order.partner_id and
                    sale_order.partner_id.id or None,
                    'user_id': sale_order.user_id and sale_order.user_id.id or
                    None,
                    'type': 'opportunity',
                    # 'description': ,
                })
        return True


class WarningAction(models.Model):
    _inherit = 'warning.action'

    options = [
        ('create_call', 'Create call phone'),
        ('create_meeting', 'Create meeting'),
        ('create_opportunity', 'Create opportunity')]

    ttype = fields.Selection(
        selection_add=options)
