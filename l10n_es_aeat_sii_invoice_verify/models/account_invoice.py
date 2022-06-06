###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import _, models
from odoo.tools import ustr


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _check_invoice(self):
        for invoice in self.filtered(lambda i: i.state in ['open', 'paid']):
            serv = invoice._connect_sii(invoice.type)
            if invoice.sii_state == 'not_sent':
                tipo_comunicacion = 'A0'
            else:
                tipo_comunicacion = 'A1'
            header = invoice._get_sii_header(tipo_comunicacion)
            inv_vals = {
                'sii_header_sent': json.dumps(header, indent=4),
            }
            try:
                inv_dict = invoice._get_sii_invoice_dict()
                inv_vals['sii_content_sent'] = json.dumps(inv_dict, indent=4)
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.ConsultaLRFacturasEmitidas(
                        header, inv_dict)
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.ConsultaLRFacturasRecibidas(
                        header, inv_dict)
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
