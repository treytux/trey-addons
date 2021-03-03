# Copyright 2020 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from lxml import etree
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
except (ImportError, IOError) as err:
    _logger.debug(err)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('transferbi', 'Transferbi')],
    )
    transferbi_username = fields.Char(
        string='Username',
        help='Used for cit.seur.com webservice (generate labels)',
    )
    transferbi_password = fields.Char(
        sting='Password',
        help='Used for cit.seur.com webservice (generate labels)',
    )

    @api.model
    def transferbi_wsdl_get(self):
        return 'http://188.93.78.56:8099/TANTAWS/Service1.asmx?WSDL'

    @api.model
    def transferbi_soap_send(self, method, *args):
        def trace(title, data):
            _logger.debug('%s %s: %s' % (
                method, title, etree.tostring(data['envelope'])))

        history = HistoryPlugin()
        client = Client(
            wsdl=self.transferbi_wsdl_get(),
            transport=Transport(),
            plugins=[history],
        )
        cli = client.bind('ServiciosTANTA', 'ServiciosTANTASoap')
        response = cli[method](*args)
        trace('Request', history.last_sent)
        trace('Response', history.last_received)
        return response

    def transferbi_test_connection(self):
        self.ensure_one()
        res = self.transferbi_soap_send(
            'GetDepartamentos',
            self.transferbi_username,
            self.transferbi_password,
        )
        return res._value_1._value_1[0]['Departamentos']['Error'] == '0'

    def transferbi_send_shipping(self, pickings):
        return [self.transferbi_create_shipping(p) for p in pickings]

    def transferbi_create_shipping(self, picking):
        self.ensure_one()
        partner = picking.partner_id
        phone = partner.phone and partner.phone.replace(' ', '') or ''
        mobile = partner.mobile and partner.mobile.replace(' ', '') or ''
        res = self.transferbi_soap_send(
            'AltaPaqueteriaPeso',
            self.transferbi_username,
            self.transferbi_password,
            '%s-%s' % (picking.partner_id.id, picking.name),
            partner.name or '',
            ' '.join([s for s in [partner.street, partner.street2] if s]),
            partner.city or '',
            partner.zip or '',
            picking.number_of_packages,
            picking.shipping_weight or 1,
            picking.name,
            '',
            ', '.join([phone, mobile]),
        )
        res = {i['string'][0]: i['string'][1] for i in res}
        if res['error'] == '-1':
            raise exceptions.UserError(
                _('Transferbi exception: %s') % res['mensajeError'])
        picking.transferbi_barcodes = ','.join([
            res[k] for k in sorted(res.keys()) if k.startswith('barCode')])
        picking.carrier_tracking_ref = res['serviceCode']
        res['tracking_number'] = picking.carrier_tracking_ref
        return res

    def transferbi_tracking_state_update(self, picking):
        self.ensure_one()
        if not self.transferbi_username:
            picking.tracking_state_history = _(
                'Status cannot be checked, enter webservice carrier '
                'credentials')
            return
        res = self.transferbi_soap_send(
            'GetEstadoAlbaran',
            self.transferbi_username,
            self.transferbi_password,
            picking.carrier_tracking_ref,
            '%s-%s' % (picking.partner_id.id, picking.name),
        )
        res = [ln['Table1'] for ln in res._value_1._value_1]
        picking.tracking_state_history = '\n'.join([
            '%s | %s' % (r['Estado'], r['TipoMov']) for r in res])
        state = res[-1:][0]['Estado']
        static_states = {
            'INICIAL': 'shipping_recorded_in_carrier',
            'EN MOVIMIENTO': 'in_transit',
            'ENTREGADO': 'customer_delivered',
        }
        picking.delivery_state = static_states.get(state, 'incidence')

    def transferbi_cancel_shipment(self, pickings):
        for picking in pickings:
            if not picking.carrier_tracking_ref:
                continue
            res = self.transferbi_soap_send(
                'EliminarAlbaran',
                self.transferbi_username,
                self.transferbi_password,
                picking.carrier_tracking_ref,
            )
            res = res._value_1._value_1[0]['Table1']
            if not res['Codigo']:
                raise exceptions.UserError(
                    _('Cancel Transferbi shipment (%s): %s') % (
                        picking.carrier_tracking_ref, res['DescCodigo']))
        return True

    def transferbi_get_tracking_link(self, picking):
        return ''
