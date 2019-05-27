# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
from openerp.modules.registry import RegistryManager
from openerp.tools import ustr
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_wsdl(self):
        self.ensure_one()
        wsdl = ''
        if self.type in ['out_invoice', 'out_refund']:
            wsdl = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.wsdl_out', False)
        elif self.type in ['in_invoice', 'in_refund']:
            wsdl = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.wsdl_in', False)
        return wsdl

    @api.multi
    def _get_test_mode(self, port_name):
        self.ensure_one()
        if self.company_id.sii_test:
            port_name += 'Pruebas'
        return port_name

    @api.multi
    def _connect_wsdl(self, wsdl, port_name):
        self.ensure_one()
        client = self._connect_sii(wsdl)
        port_name = self._get_test_mode(port_name)
        serv = client.bind('siiService', port_name)
        return serv

    @api.multi
    def _send_soap(self, wsdl, port_name, operation, param1, param2):
        self.ensure_one()
        serv = self._connect_wsdl(wsdl, port_name)
        res = serv[operation](param1, param2)
        return res

    @api.multi
    def _check_invoice(self):
        for invoice in self.filtered(lambda i: i.state in ['open', 'paid']):
            wsdl = invoice._get_wsdl()
            if invoice.type in ['out_invoice', 'out_refund']:
                port_name = 'SuministroFactEmitidas'
                operation = 'ConsultaLRFacturasEmitidas'
                number = invoice.number[0:60]
            elif invoice.type in ['in_invoice', 'in_refund']:
                port_name = 'SuministroFactRecibidas'
                operation = 'ConsultaLRFacturasRecibidas'
                number = invoice.supplier_invoice_number and \
                    invoice.supplier_invoice_number[0:60]
            if invoice.sii_state == 'not_sent':
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'
            header = invoice._get_sii_header(tipo_comunicacion)
            fiscal_year = fields.Date.from_string(
                invoice.period_id.fiscalyear_id.date_start).year
            period = '%02d' % fields.Date.from_string(
                invoice.period_id.date_start).month
            invoice_date = invoice._change_date_format(invoice.date_invoice)
            try:
                query = {
                    "IDFactura": {
                        "NumSerieFacturaEmisor": number,
                        "FechaExpedicionFacturaEmisor": invoice_date}}
                if header['IDVersionSii'] == '1.0':
                    query['PeriodoImpositivo'] = {
                        "Ejercicio": fiscal_year,
                        "Periodo": period}
                else:
                    query['PeriodoLiquidacion'] = {
                        "Ejercicio": fiscal_year,
                        "Periodo": period}
                res = invoice._send_soap(
                    wsdl, port_name, operation, header, query)
                inv_vals = {'sii_header_sent': json.dumps(header, indent=4)}
                if invoice.type in ['out_invoice', 'out_refund']:
                    answer = res['RegistroRespuestaConsultaLRFacturasEmitidas']
                else:
                    answer = res[
                        'RegistroRespuestaConsultaLRFacturasRecibidas']
                if len(answer) < 1:
                    inv_vals['sii_send_error'] = _(
                        'Without answer. Try send it again to the SII.')
                else:
                    reg_state = answer[0]['EstadoFactura']['EstadoRegistro']
                    csv = answer[0]['DatosPresentacion']['CSV']
                    if reg_state == 'Correcta':
                        inv_vals.update({
                            'sii_state': 'sent',
                            'sii_csv': csv,
                            'sii_send_failed': False})
                    elif reg_state == 'AceptadaConErrores':
                        inv_vals.update({
                            'sii_state': 'sent_w_errors',
                            'sii_csv': csv,
                            'sii_send_failed': True})
                    else:
                        inv_vals['sii_send_failed'] = True
                    inv_vals['sii_return'] = res
                    send_error = False
                    error_code = answer[0]['EstadoFactura'][
                        'CodigoErrorRegistro']
                    error_desc = answer[0]['EstadoFactura'][
                        'DescripcionErrorRegistro']
                    if error_code:
                        send_error = u"{} | {}".format(
                            unicode(error_code), unicode(error_desc)[:60])
                    inv_vals['sii_send_error'] = send_error
                invoice.write(inv_vals)
            except Exception as fault:
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(self.id)
                inv_vals.update({
                    'sii_send_failed': True,
                    'sii_send_error': ustr(fault),
                    'sii_return': ustr(fault)})
                invoice.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def verify_sii(self):
        invoices = self.filtered(lambda i: i.sii_enabled)
        for invoice in invoices:
            if invoice.company_id.sii_enabled:
                invoice._check_invoice()
