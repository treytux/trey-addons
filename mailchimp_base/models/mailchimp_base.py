# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
#
from openerp import models, fields, api, _, exceptions
import logging
_log = logging.getLogger(__name__)

try:
    import mailchimp
except ImportError:
    _log.warning('mailchimp python lib not installed.')


class MailchimpList(models.Model):
    _name = 'mailchimp.list'
    _description = 'Mailchimp list'

    name = fields.Char(
        string='Name'
    )


class MailchimpMapLine(models.Model):
    _name = 'mailchimp.map.line'
    _description = 'Mailchimp map line'

    name = fields.Char(
        string='Name'
    )
    config_id = fields.Many2one(
        comodel_name='mailchimp.config',
        string='Configuration'
    )
    field_odoo = fields.Char(
        string='Field Odoo'
    )
    field_mailchimp = fields.Char(
        string='Field MailChimp'
    )


class MailchimpConfig(models.Model):
    _name = 'mailchimp.config'
    _description = 'Mailchimp configuration'

    name = fields.Char(
        string='Name'
    )
    mapi = fields.Char(
        string='API',
        required=True
    )
    subscription_list = fields.Char(
        string='Subscription List'
    )
    map_line_ids = fields.One2many(
        comodel_name='mailchimp.map.line',
        inverse_name='config_id',
        string='Map lines',
        required=True
    )

    # Abre el asistente para seleccionar una de las listas de suscripcion
    # disponibles
    @api.multi
    def buttonChangeList(self):
        cr, uid, context = self.env.args
        change_list = self.env['mailchimp.change.list'].create({})
        self.env['mailchimp.change.list'].actionGetLists()

        return {
            'name': 'Subscription lists',
            'type': 'ir.actions.act_window',
            'res_model': 'mailchimp.change.list',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': change_list.id,
            'nodestroy': True,
            'target': 'new',
            'context': context,
        }

    # Obtener la lista de subscriptores de la configuracion
    def getSubscriptionListId(self, mapi):
        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            raise exceptions.Warning(
                _('You must define a configuration for your Mailchimp '
                  'account.')
            )
        else:
            if len(mailchimp_config) > 0:
                subscription_list_name = mailchimp_config.subscription_list
                try:
                    # Obtener las listas de subscripcion
                    lists = mapi.lists.list()
                except:
                    raise exceptions.Warning(
                        _('Data error Mailchimp connection, review the '
                          'configuration in Configuration/Mailchimp/Mailchimp '
                          'configuration menu.')
                    )

                # Inicializar por si no la encuentra
                list_id = 0

                for l in lists['data']:
                    if l['name'] == subscription_list_name:
                        list_id = l['id']
                        break
                if list_id == 0:
                    raise exceptions.Warning(
                        _('The list \'%s\' does not exist in Mailchimp.' %
                            (subscription_list_name))
                    )
                return list_id

    # Comprueba si conecta o no
    @api.multi
    def isConnected(self):
        # Conectar
        mapi = self.connect()

        # Obtener las lista de subscripcion definida en la configuracion
        self.getSubscriptionListId(mapi)

        return True

    @api.one
    def testConnect(self):
        res = self.isConnected()
        if res:
            raise exceptions.Warning(
                _('The connection was made successfully.')
            )
        return True

    @api.model
    def create(self, data):
        # Comprobar que solo hay un registro de configuracion de mailchimp
        if len(self.env['mailchimp.config'].search([])) >= 1:
            raise exceptions.Warning(
                _('There can be only one configuration of Mailchimp in the '
                    'system.')
            )

        return super(MailchimpConfig, self).create(data)

    @api.multi
    def write(self, vals):
        res = super(MailchimpConfig, self).write(vals)
        if not res:
            return res

        # Para evitar errores, comprobar que los datos de conexion son
        # correctos antes de escribir (pero hay que comprobar los valores que
        # acaban de introducir)

        # Obtener el campo mapi de vals (por si lo han modificado) o de la
        # configuracion que ya estaba almacenada
        mapi_id = vals.get('mapi', self.mapi)
        mapi = mailchimp.Mailchimp(mapi_id)

        # Buscar lista subscripcion
        try:
            # Obtener las listas de subscripcion
            lists = mapi.lists.list()
        except:
            raise exceptions.Warning(
                _('Data error Mailchimp connection, review the '
                  'configuration in Configuration/Mailchimp/Mailchimp '
                  'configuration menu.')
            )

        # Inicializar por si no la encuentra
        list_id = 0
        # Obtener el campo subscription_list de vals (por si lo han modificado)
        # o de la configuracion que ya estaba almacenada
        subscription_list_name = vals.get(
            'subscription_list', self.subscription_list)

        for l in lists['data']:
            if l['name'] == subscription_list_name:
                list_id = l['id']
                break
        if list_id == 0:
            raise exceptions.Warning(
                _('The list \'%s\' does not exist in Mailchimp.' %
                    (subscription_list_name))
            )
        return res

    ########################################################################
    # Funciones necesarias para las operaciones con la API de Mailchimp
    ########################################################################
    # Obtener listas diponibles
    def getLists(self, mapi):
        try:
            return mapi.lists.list()
        except:
            raise exceptions.Warning(
                _('Data error Mailchimp connection, review the '
                  'configuration in Configuration/Mailchimp/Mailchimp '
                  'configuration menu.')
            )

    # Comprueba si la lista existe
    def existsList(self, mapi, list_name):
        for l in self.getLists(mapi)['data']:
            if l['name'] == list_name:
                return True
        _log.error(_('The list does %s not exist.' % list_name))

    # Devuelve el id de una lista
    def getListId(self, mapi, list_name):
        self.existsList(mapi, list_name)
        for l in self.getLists(mapi)['data']:
            if l['name'] == list_name:
                return l['id']
        return 0

    # Obtener configuracion de MailChimp
    def getConfiguration(self):
        # Comprobar si existe configuracion para mailchimp
        mailchimp_configs = self.env['mailchimp.config'].search([])
        if not mailchimp_configs:
            _log.warning(
                _('Not exists configuration of Mailchimp in the system.\n'
                  'Make sure you have saved the settings.')
            )
            return False
        return mailchimp_configs[0]

    # Conecta con MailChimp
    def connect(self):
        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            return False
        else:
            try:
                # Conectar
                mapi = mailchimp.Mailchimp(mailchimp_config.mapi)
            except:
                raise exceptions.Warning(
                    _('Data error Mailchimp connection, review the '
                      'configuration in Configuration/Mailchimp/Mailchimp '
                      'configuration menu.')
                )

            return mapi

    # Comprueba si hay que exportar los datos del partner basandose en los
    # datos de configuracion
    def checkExportData(self, partner):
        # Comprobar si tiene cporreo
        if not partner.email:
            return False

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            return False
        else:
            # Customers: customer and is_company
            if mailchimp_config.customers is True \
               and partner.customer is True and partner.is_company is True:
                return True

            # Suppliers: suppliers and is_company
            if mailchimp_config.suppliers is True \
               and partner.supplier is True and partner.is_company is True:
                return True

            # Customer contacts: customer and not is_company
            if mailchimp_config.customer_contacts is True \
               and partner.customer is True and partner.is_company is False:
                return True

            # Supplier contacts: supplier and not is_company
            if mailchimp_config.supplier_contacts is True \
               and partner.supplier is True and partner.is_company is False:
                return True

            return False

    # Comprueba si un id de mailchimp (leid) esta dado de alta en una lista
    def existLeid(self, leid):
        # Conectar
        mapi = self.connect()
        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            return False
        else:
            # Obtener id de la lista
            list_id = self.env['mailchimp.config'].getListId(
                mapi, mailchimp_config.subscription_list)

            try:
                leid = int(leid)
            except:
                leid = leid

            data_clients = mapi.lists.members(list_id)
            if 'data' in data_clients:
                for c in data_clients['data']:
                    if leid == c['leid']:
                        return True
            return False

    # Crear un suscriptor en una lista a partir de un correo
    def createSubscriptor(self, email, vals):
        # Conectar con MailChimp
        mapi = self.connect()

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            return False
        else:
            # Obtener id de la lista
            list_id = self.env['mailchimp.config'].getListId(
                mapi, mailchimp_config.subscription_list)

            # double_optin=False: para que no pida confirmacion al usuario para
            # crear la subscripcion
            try:
                res = mapi.lists.subscribe(
                    list_id, {'email': email}, vals, double_optin=False,
                    update_existing=True)
                _log.info(_('%s updated to %s in the list: %s' % (
                    {'email': email}, vals, list_id)))
                return res
            except Exception as e:
                raise exceptions.Warning(
                    _('Mailchimp error in partner with email: \'%s\'.\n'
                      '%s' % (email, e)))

    # Actualizar un suscriptor en una lista a partir de leid
    def updateSubscriptor(self, leid, vals):
        # Conectar con MailChimp
        mapi = self.connect()

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            return False
        else:
            # Obtener id de la lista
            list_id = self.env['mailchimp.config'].getListId(
                mapi, mailchimp_config.subscription_list)

            # double_optin=False: para que no pida confirmacion al usuario para
            # crear la subscripcion
            try:
                res = mapi.lists.subscribe(
                    list_id, {'leid': leid}, vals, double_optin=False,
                    update_existing=True)
                _log.info(_('%s updated to %s in the list: %s' % (
                    {'leid': leid}, vals, list_id)))
                return res
            except Exception as e:
                raise exceptions.Warning(
                    _('Mailchimp error in partner with vals: \'%s\'.\n'
                      '%s' % (vals, e)))

    # Eliminar un suscriptor en una lista a partir de leid
    def deleteSubscriptor(self, leid):
        # Conectar con MailChimp
        mapi = self.connect()

        # Obtener configuracion
        mailchimp_config = self.getConfiguration()
        if not mailchimp_config:
            return False
        else:
            # Obtener id de la lista
            list_id = self.env['mailchimp.config'].getListId(
                mapi, mailchimp_config.subscription_list)

            # delete_member=True Para que lo elimine
            # send_goodbye=False Para que no envie correo de despedida
            # send_notify=False Para que no envie correo de notificacion
            try:
                res = mapi.lists.unsubscribe(
                    list_id, {'leid': leid}, delete_member=True,
                    send_goodbye=False, send_notify=False)
                _log.info(_('%s deleted in the list %s' % (
                    {'leid': leid}, list_id)))
                return res
            except Exception as e:
                raise exceptions.Warning(
                    _('Mailchimp error in partner.\n'
                      '%s' % e)
                )
