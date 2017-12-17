# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _, exceptions
import logging
_log = logging.getLogger(__name__)

try:
    import mailchimp
except ImportError:
    _log.warning('mailchimp python lib not installed.')


class MailchimpChangeList(models.TransientModel):
    _name = 'mailchimp.change.list'
    _description = 'Mailching change list'

    name = fields.Char(string='Emmpty')
    subscription_list_id = fields.Many2one(
        comodel_name='mailchimp.list',
        string='Subscription list',
        help="Available lists MailChimp API."
    )

    # Cargar listas de suscripcion disponibles
    def actionGetLists(self):
        # Buscar config mailchimp
        mailchimps = self.env['mailchimp.config'].search([])
        if mailchimps:
            # Siempre conecta, pero para saber si los datos de la API o la
            # lista de suscripcion son correctos, necesitamos ejecutar las
            # siguientes funciones
            try:
                # Conectar
                mapi = mailchimp.Mailchimp(mailchimps[0].mapi)

                # Eliminar los registros de la tabla por si las listas han
                # cambiado
                mailchimp_lists = self.env['mailchimp.list'].search([])
                for mailchimp_list in mailchimp_lists:
                    mailchimp_list.unlink()

                # Obtener las listas de subscripcion
                lists = mapi.lists.list()

                # Crear registros de listas
                for l in lists['data']:
                    data = {
                        'name': l['name'],
                    }
                    self.env['mailchimp.list'].create(data)
            except:
                raise exceptions.Warning(
                    _('Data error Mailchimp connection.')
                )

        else:
            raise exceptions.Warning(
                _('Not exists configuration of Mailchimp in the system. '
                  'Make sure you have saved the settings.')
            )

    # Escribir la lista seleccionada en el campo lista de suscripcion de la
    # configuracion
    @api.one
    def buttonAccept(self):
        # Buscar config mailchimp
        mailchimps = self.env['mailchimp.config'].search([])
        if mailchimps:
            record = self.env['mailchimp.config'].browse(mailchimps[0].id)
            record.write({'subscription_list': self.subscription_list_id.name})
        else:
            raise exceptions.Warning(_(
                'Not exists configuration of Mailchimp in the system.\n'
                'Make sure you have saved the settings.')
            )

        return {'type': 'ir.actions.act_window_close'}
