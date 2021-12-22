###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import _, models
from odoo.tools import ustr


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_wsdl(self):
        wsdl = ''
        if self.type in ['out_invoice', 'out_refund']:
            wsdl = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.wsdl_out', False)
        elif self.type in ['in_invoice', 'in_refund']:
            wsdl = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.wsdl_in', False)
        return wsdl

    def _get_test_mode(self, port_name):
        if self.company_id.sii_test:
            port_name += 'Pruebas'
        return port_name

    def _connect_wsdl(self, wsdl, port_name):
        client = self._connect_sii(wsdl)
        port_name = self._get_test_mode(port_name)
        serv = client.bind('siiService', port_name)
        return serv

    def _send_soap(self, wsdl, port_name, operation, param1, param2):
        serv = self._connect_wsdl(wsdl, port_name)
        res = serv[operation](param1, param2)
        return res

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
            fiscal_year = invoice.date_invoice.year
            period = '%02d' % invoice.date_invoice.month
            invoice_date = invoice._change_date_format(invoice.date_invoice)
            inv_vals = {}
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
                # inv_vals = {'sii_header_sent': json.dumps(header, indent=4)}
                inv_vals['sii_header_sent'] = json.dumps(header, indent=4)
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
                            error_code, error_desc)[:60]
                    inv_vals['sii_send_error'] = send_error
                invoice.write(inv_vals)
            except Exception as fault:
                inv_vals.update({
                    'sii_send_failed': True,
                    'sii_send_error': ustr(fault),
                    'sii_return': ustr(fault)})
                invoice.write(inv_vals)
                raise

    def verify_sii(self):
        invoices = self.filtered(lambda i: i.sii_enabled)
        for invoice in invoices:
            if invoice.company_id.sii_enabled:
                invoice._check_invoice()
