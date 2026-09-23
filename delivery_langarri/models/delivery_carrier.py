###############################################################################
# For copyright and license notices, see __manifest__.py file in root
###############################################################################
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import requests
from odoo import _, exceptions, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[
            ('langarri', 'Langarri'),
        ],
        ondelete={
            'langarri': 'set default',
        },
    )
    langarri_customer_code = fields.Char(
        string='Customer code',
        help='Parameter wCODCliente',
    )
    langarri_username = fields.Char(
        string='Username',
        help='Parameter wUsuario',
    )
    langarri_password = fields.Char(
        string='Password',
        help='Parameter wClave',
    )
    langarri_rem_name = fields.Char(
        string='Sender name',
        help='Parameter wNOMREM. If not set, company name will be used.',
    )
    langarri_charge_type = fields.Selection(
        selection=[
            ('P', 'Prepaid'),
            ('D', 'Collect'),
        ],
        default='P',
        string='Charge type',
        help='Parameter wPDBIDO',
    )
    langarri_ignore_errors = fields.Selection(
        selection=[
            ('S', 'Yes'),
            ('N', 'No'),
        ],
        default='N',
        string='Ignore validation errors',
        help='Parameter wIgnorarErrores',
    )
    langarri_label_format = fields.Selection(
        selection=[
            ('pdf', 'PDF'),
            ('zpl', 'ZPL'),
        ],
        default='pdf',
        required=True,
        string='Label format',
    )
    langarri_test_url = fields.Char(
        string='Test URL',
        default='http://movil.langarri.es:8089/Wsintegracioneslangarri.asmx/',
    )
    langarri_prod_url = fields.Char(
        string='Production URL',
        default='http://movil.langarri.es:8089/Wsintegracioneslangarri.asmx/',
    )

    def _langarri_base_url(self):
        self.ensure_one()
        base = (
            self.langarri_prod_url if self.prod_environment
            else self.langarri_test_url)
        return (base or '').rstrip('/') + '/'

    def _langarri_endpoint(self, method):
        return urljoin(self._langarri_base_url(), method)

    def _langarri_request(self, method, params):
        url = self._langarri_endpoint(method)
        response = requests.get(url, params=params, timeout=30)
        return url, response

    def _langarri_prepare_shipping(self, picking):
        self.ensure_one()
        company_partner = picking.company_id.partner_id
        company_street = (
            company_partner.street or '' + company_partner.street2 or '')
        partner = picking.partner_id
        partner_street = partner.street or '' + partner.street2 or ''
        if not partner.zip or not partner.city:
            raise exceptions.UserError(_(
                'Partner postal code and city is required.'))
        shipping_weight = (
            picking.shipping_weight
            and round(picking.weight_uom_id._compute_quantity(
                picking.shipping_weight, self.env.ref('uom.product_uom_kgm')))
            or 1)
        packages = picking.number_of_packages or 1
        ref = (
            picking.sale_id and picking.sale_id.name or picking.origin
            or picking.name)
        obs = picking.note or picking.sale_id and picking.sale_id.note or ''
        return {
            'wCODCliente': self.langarri_customer_code or '',
            'wREFALB': ref or '',
            'wFECALB': fields.Datetime.now().strftime('%d/%m/%Y'),
            'wOBSALB': obs[:4000],
            'wNOMREM': self.langarri_rem_name or company_partner.name,
            'wCPREM': company_partner.zip,
            'wPOBREM': company_partner.city,
            'wDIRREM': company_street[:50],
            'wPROREM': (
                company_partner.state_id and company_partner.state_id.code
                or ''),
            'wPaisesREM': (
                company_partner.country_id and company_partner.country_id.code
                or ''),
            'wArticulo': 'MDIA',
            'wTIPALB': '',
            'wVIAREM': '',
            'wNUMREM': '',
            'wPISOREM': '',
            'wTLFREM': company_partner.phone,
            'wMOVILREM': company_partner.mobile,
            'wEMAILREM': company_partner.email,
            'wOBSREM': '',
            'wNOMDES': partner.display_name[:60],
            'wCPDES': partner.zip or '',
            'wPOBDES': partner.city or '',
            'wPRODES': partner.state_id and partner.state_id.name or '',
            'wPaisesDES': (
                partner.country_id and partner.country_id.name or ''),
            'wVIADES': '',
            'wNUMDES': '',
            'wPISODES': '',
            'wDNIDES': '',
            'wDIRDES': partner_street[:50],
            'wTLFDES': partner.phone,
            'wMOVILDES': partner.mobile,
            'wEMAILD': partner.email,
            'wBUL': packages,
            'wKIL': round(shipping_weight, 2),
            'wPESOVOL': '',
            'wALTO': '',
            'wANCHO': '',
            'wLARGO': '',
            'wSABADO': '',
            'wCONRETORNO': '',
            'wPDBIDO': self.langarri_charge_type,
            'wANTICIPO': '',
            'wREEMB': '',
            'wREEMB': '',
            'wVALMER': '',
            'wGESTDES': '',
            'wGESTREM': '',
            'wCOCLI': '',
            'wHORAINI': '',
            'wHORAFIN': '',
            'wHORAINITARDES': '',
            'wHORAFINTARDES': '',
            'wNoApilable': '',
            'wDAC': '',
            'wTipoMercancia': '',
            'wIgnorarErrores': self.langarri_ignore_errors,
            'wUsuario': self.langarri_username or '',
            'wClave': self.langarri_password or '',
            'wCodDepartamento': '',
        }

    def _langarri_raise_from_errors(self, error_node):
        if error_node is None:
            return
        messages = []
        for child in list(error_node):
            text = ''.join(child.itertext()).strip()
            if text:
                messages.append(text)
        if messages:
            raise exceptions.UserError('\n'.join(messages))

    def _langarri_parse_shipping_response(self, response_text):
        root = ET.fromstring(response_text or '<empty/>')
        tracking_number = root.findtext('.//Albaran')
        barcode = root.findtext('.//CodigoBarras')
        packages = [
            x.text for x in root.findall('.//CodigoBarrasBulto') if x.text]
        self._langarri_raise_from_errors(root.find('.//ControlErrores'))
        if not tracking_number:
            raise exceptions.UserError(_(
                'Langarri do not return tracking number.'))
        return tracking_number, barcode, packages

    def langarri_send_shipping(self, pickings):
        results = []
        for picking in pickings:
            data = self._langarri_prepare_shipping(picking)
            url, resp = self._langarri_request('GrabarEnvio', data)
            picking.langarri_last_request = '%s?%s' % (
                url, resp.request.body or resp.request.url.split('?', 1)[-1])
            picking.langarri_last_response = resp.text
            if resp.status_code != 200:
                raise exceptions.UserError(_(
                    'Error %s in Langarri request') % resp.status_code)
            tracking_number, barcode, packages = (
                self._langarri_parse_shipping_response(resp.text))
            picking.tracking_number = tracking_number
            picking.langarri_barcode = barcode
            picking.langarri_package_barcodes = '\n'.join(packages)
            picking.carrier_tracking_ref = barcode
            self.langarri_get_label(picking)
            results.append({
                'exact_price': 0,
                'tracking_number': barcode,
            })
        return results

    def langarri_modify_shipping(self, pickings):
        results = []
        for picking in pickings:
            if (not picking.tracking_number
                    or picking.delivery_type != 'langarri'):
                raise exceptions.UserError(_(
                    'Langarri tracking number is required to modify '
                    'the shipment.')
                )
            data = self._langarri_prepare_shipping(picking)
            data.update({
                'wALB': picking.tracking_number,
            })
            url, resp = self._langarri_request('ModificarEnvio', data)
            picking.langarri_last_request = '%s?%s' % (
                url, resp.request.body or resp.request.url.split('?', 1)[-1])
            picking.langarri_last_response = resp.text
            if resp.status_code != 200:
                raise exceptions.UserError(_(
                    'Error %s in Langarri request') % resp.status_code)
            tracking_number, barcode, packages = (
                self._langarri_parse_shipping_response(resp.text))
            picking.tracking_number = tracking_number
            picking.langarri_barcode = barcode
            picking.langarri_package_barcodes = '\n'.join(packages)
            picking.carrier_tracking_ref = barcode
            self.langarri_get_label(picking)
            results.append({
                'exact_price': 0,
                'tracking_number': barcode,
            })
        return results

    def langarri_get_label(self, picking):
        if not picking.tracking_number:
            return False
        params = {
            'wAlbaran': picking.tracking_number,
            'wAlbaranDesde': picking.tracking_number,
            'wReferenciaAlbaran': '',
            'wUsuario': self.langarri_username or '',
            'wClave': self.langarri_password or '',
        }
        url, resp = self._langarri_request('EtiquetaEnvio', params)
        picking.langarri_last_request = '%s?%s' % (
            url, resp.request.url.split('?', 1)[-1])
        picking.langarri_last_response = resp.text
        if resp.status_code != 200:
            picking.message_post(body=_(
                'Error %s in label request') % resp.status_code)
            return False
        root = ET.fromstring(resp.text or '<empty/>')
        self._langarri_raise_from_errors(root.find('.//ControlErrores'))
        if self.langarri_label_format == 'zpl':
            label_data_b64 = root.findtext('.//Imagen64')
            file_ext = 'zpl'
            mimetype = 'text/plain'
        else:
            label_data_b64 = root.findtext('.//Imagen64')
            file_ext = 'pdf'
            mimetype = 'application/pdf'
        if not label_data_b64:
            return False
        self.env['ir.attachment'].create({
            'name': 'langarri_%s.%s' % (picking.tracking_number, file_ext),
            'datas': label_data_b64,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'mimetype': mimetype,
        })
        return label_data_b64

    def langarri_cancel_shipment(self, pickings):
        results = []
        for picking in pickings:
            if not picking.tracking_number:
                raise exceptions.UserError(_(
                    'Langarri tracking number is required to cancel '
                    'the shipment.')
                )
            params = {
                'wAlbaran': picking.tracking_number,
                'wReferenciaAlbaran': '',
                'wUsuario': self.langarri_username or '',
                'wClave': self.langarri_password or '',
            }
            url, resp = self._langarri_request('BorrarEnvio', params)
            picking.langarri_last_request = '%s?%s' % (
                url, resp.request.url.split('?', 1)[-1])
            picking.langarri_last_response = resp.text
            if resp.status_code != 200:
                raise exceptions.UserError(_(
                    'Error %s in Langarri request') % resp.status_code)
            root = ET.fromstring(resp.text or '<empty/>')
            self._langarri_raise_from_errors(root.find('.//ControlErrores'))
            results.append(True)
        return results

    def langarri_tracking_state_update(self, picking):
        raise NotImplementedError()

    def langarri_get_tracking_link(self, picking):
        raise NotImplementedError()

    def langarri_rate_shipment(self, order):
        raise NotImplementedError()
