###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from datetime import datetime, timedelta
from unicodedata import normalize

import requests
from odoo import _, exceptions, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('tipsa', 'Tipsa')],
    )
    tipsa_usercode = fields.Char(
        string='User code',
        help='User code for Tipsa webservice',
    )
    tipsa_password = fields.Char(
        string='Password',
        help='Password for Tipsa webservice',
    )
    tipsa_agency_code = fields.Char(
        strig='Agency code',
    )
    tipsa_token = fields.Char(
        string='Access token',
        help='Access token. Valid for 15 minutes',
    )
    tipsa_token_expiration = fields.Datetime(
        string='Access Token Validity',
        default=fields.Datetime.now,
    )
    tipsa_service_code = fields.Selection(
        selection=[
            ('48', '48'),
            ('92', '92'),
        ],
        default='48',
        string='Tipsa service code',
    )
    tipsa_test_url_login = fields.Char(
        string='URL test login',
        default='https://testapps.tipsa-dinapaq.com/SOAP?service='
                'LoginWSService',
    )
    tipsa_url_login = fields.Char(
        string='URL login',
        default='https://apps.tipsa-dinapaq.com/SOAP?service=LoginWSService',
    )
    tipsa_test_url_webservice = fields.Char(
        string='URL test webservice',
        default='https://testapps.tipsa-dinapaq.com/SOAP?'
                'service=WebServService',
    )
    tipsa_url_webservice = fields.Char(
        string='URL webservice',
        default='https://apps.tipsa-dinapaq.com/SOAP?service=WebServService',
    )
    allow_labelary = fields.Boolean(
        string='Allow Labelary API',
        help='Allow connect to Labelary API to '
             'obtain PDF international labels',
    )

    def normalize_text(self, text):
        return text and normalize(
            "NFKD", text).encode("ascii", "ignore").decode("ascii") or None

    def tipsa_authenticate(self):
        if self.tipsa_token_expiration > datetime.now():
            return self.tipsa_token
        headers = {
            'Content-type': 'text/xml',
        }
        line_1 = '<soap:Envelope '
        line_2 = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"'
        line_3 = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        line_4 = 'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        xml = """<?xml version="1.0" encoding="utf-8"?>
            %s %s
            <soap:Body>
                <LoginWSService___LoginCli>
                <strCodAge>%s</strCodAge>
                <strCod>%s</strCod>
                <strPass>%s</strPass>
                </LoginWSService___LoginCli>
            </soap:Body>
            </soap:Envelope>""" % (
            line_1 + line_2,
            line_3 + line_4,
            self.tipsa_agency_code,
            self.tipsa_usercode,
            self.tipsa_password,
        )
        if self.prod_environment:
            url = self.tipsa_url_login
        else:
            url = self.tipsa_test_url_login
        res = requests.post(url, headers=headers, data=xml)
        if res.status_code != 200:
            raise exceptions.UserError(
                _('Tipsa exception: %s, %s') % res.status_code, res.reason)
        token_start = res.text.find('<ID>{')
        token_end = res.text.find('}</ID>')
        self.tipsa_token = res.text[token_start + 5:token_end]
        self.tipsa_token_expiration = datetime.now() + timedelta(minutes=13)
        return res.text[token_start + 5:token_end]

    def tipsa_send(self, data):
        headers = {
            'Content-type': 'application/json',
        }
        if self.prod_environment:
            url = self.tipsa_url_webservice
        else:
            url = self.tipsa_test_url_webservice
        res = requests.post(url, headers=headers, data=data)
        return res

    def tipsa_send_shipping(self, pickings):
        return [self.tipsa_create_shipping(p) for p in pickings]

    def create_attachment(self, picking_id, datas_fname, data_content, ftype):
        mimetype = ftype == 'pdf' and 'application/pdf' or 'application/txt'
        self.env['ir.attachment'].create({
            'name': datas_fname,
            'datas': data_content,
            'datas_fname': datas_fname,
            'res_model': 'stock.picking',
            'res_id': picking_id,
            'mimetype': mimetype,
        })

    def _tipsa_prepare_create_shipping(self, picking, token_id):
        self.ensure_one()
        picking_date = datetime.now().strftime("%Y/%m/%d")
        line_1 = '<soap:Envelope '
        line_2 = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"'
        line_3 = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        line_4 = 'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        xml = """<?xml version="1.0" encoding="utf-8"?>
            %s %s
            <soap:Header>
                <ROClientIDHeader>
                <ID>{%s}</ID>
                </ROClientIDHeader>
            </soap:Header>
            <soap:Body>
                <WebServService___GrabaEnvio20>
                <strCodAgeCargo>%s</strCodAgeCargo>
                <strCodAgeOri>%s</strCodAgeOri>
                <dtFecha>%s</dtFecha>
                <strCodTipoServ>%s</strCodTipoServ>
                <strCodCli>%s</strCodCli>
                <strNomOri>%s</strNomOri>
                <strDirOri>%s</strDirOri>
                <strPobOri>%s</strPobOri>
                <strCPOri>%s</strCPOri>
                <strTlfOri>%s</strTlfOri>
                <strNomDes>%s</strNomDes>
                <strDirDes>%s</strDirDes>
                <strObs>%s</strObs>
                <strCPDes>%s</strCPDes>
                <strPobDes>%s</strPobDes>
                <strTlfDes>%s</strTlfDes>
                <intPaq>1</intPaq>
                <strPersContacto>%s</strPersContacto>
                <boDesSMS>0</boDesSMS>
                <boDesEmail>1</boDesEmail>
                <strDesDirEmails>%s</strDesDirEmails>
                <strCodPais>%s</strCodPais>
                <strContenido>%s</strContenido>
                <boInsert>1</boInsert>
                </WebServService___GrabaEnvio20>
            </soap:Body>
            </soap:Envelope>""" % (
            line_1 + line_2,
            line_3 + line_4,
            token_id,
            self.tipsa_agency_code,
            self.tipsa_agency_code,
            picking_date,
            self.tipsa_service_code,
            picking.company_id.zip,
            picking.company_id.display_name[:25],
            picking.company_id.street[:25],
            picking.company_id.city[:25],
            picking.company_id.zip,
            picking.company_id.phone,
            picking.partner_id.display_name[:25],
            picking.partner_id.street[:70],
            picking.sale_id.name,
            picking.partner_id.zip,
            picking.partner_id.city[:25],
            picking.partner_id.phone,
            picking.partner_id.display_name[:25],
            picking.company_id.email,
            picking.partner_id.country_id.code,
            picking.sale_id.name,
        )
        return self.normalize_text(xml)

    def _zebra_label_custom(self, label):
        return label

    def get_label(self, picking, token_id):
        line_1 = '<soap:Envelope '
        line_2 = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"'
        line_3 = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        line_4 = 'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        if self.prod_environment:
            url = self.tipsa_url_webservice
        else:
            url = self.tipsa_test_url_webservice
        headers = {
            'Content-type': 'text/xml',
        }
        xml = """<?xml version="1.0" encoding="utf-8"?>
            %s %s
            <soap:Header>
                <ROClientIDHeader>
                <ID>{%s}</ID>
                </ROClientIDHeader>
            </soap:Header>
            <soap:Body>
            <WebServService___ConsEtiquetaEnvio7>
            <strCodAgeOri>%s</strCodAgeOri>
            <strAlbaran>%s</strAlbaran>
            <intIdRepDet>233</intIdRepDet>
            <strFormato>pdf</strFormato>
            </WebServService___ConsEtiquetaEnvio7>
            </soap:Body>
            </soap:Envelope>""" % (
            line_1 + line_2,
            line_3 + line_4,
            token_id,
            self.tipsa_agency_code,
            picking.tipsa_picking_reference,
        )
        datas_fname = 'tipsa_%s.pdf' % picking.carrier_tracking_ref
        response = requests.post(url, headers=headers, data=xml)
        label_start = response.text.find('<v1:strEtiqueta>')
        label_end = response.text.find('</v1:strEtiqueta>')
        if label_start == -1 or label_end == -1:
            raise exceptions.UserError(
                _('Tipsa: error getting the national labels: %s') % (
                    response.text))
        label_content = response.text[label_start + 16:label_end]
        self.create_attachment(picking.id, datas_fname, label_content, 'pdf')
        if (picking.partner_id.country_id
                and picking.partner_id.country_id.code != 'ES'):
            xml = """<?xml version="1.0" encoding="utf-8"?>
                %s %s
                <soap:Header>
                    <ROClientIDHeader>
                    <ID>{%s}</ID>
                    </ROClientIDHeader>
                </soap:Header>
                <soap:Body>
                <WebServService___ImprimeEtiquetaInternacional>>
                <strCodAgeCargo>%s</strCodAgeCargo>
                <strCodAgeOri>%s</strCodAgeOri>
                <strAlbaran>%s</strAlbaran>
                </WebServService___ImprimeEtiquetaInternacional>
                </soap:Body>
                </soap:Envelope>""" % (
                line_1 + line_2,
                line_3 + line_4,
                token_id,
                self.tipsa_agency_code,
                self.tipsa_agency_code,
                picking.tipsa_picking_reference,
            )
            response = requests.post(url, headers=headers, data=xml)
            label_start = response.text.find('<v1:strEtiquetaOut>')
            label_end = response.text.find('</v1:strEtiquetaOut>')
            if label_start == -1 or label_end == -1:
                raise exceptions.UserError(
                    _('Tipsa: error getting the international labels: %s') % (
                        response.text))
            zpl_str = response.text[label_start + 19:label_end]
            if not self.allow_labelary:
                datas_fname = 'tipsa_international_%s.zpl' % (
                    picking.carrier_tracking_ref)
                self.create_attachment(picking.id, datas_fname, zpl_str, 'txt')
                return
            zpl_data = base64.decodestring(zpl_str.encode('utf-8'))
            url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4.2x5.6/0/'
            files = {'file' : zpl_data}
            headers = {'Accept' : 'application/pdf'}
            labelary_response = requests.post(
                url, headers=headers, files=files, stream=True)
            if labelary_response.status_code == 200:
                datas_fname = 'tipsa_international_%s.pdf' % (
                    picking.carrier_tracking_ref)
                pdf_data = base64.b64encode(labelary_response.content)
                self.create_attachment(
                    picking.id, datas_fname, pdf_data, 'pdf')
            else:
                picking.message_post(body=_('Could not convert PDF from ZPL'))
                datas_fname = 'tipsa_international_%s.zpl' % (
                    picking.carrier_tracking_ref)
                self.create_attachment(picking.id, datas_fname, zpl_str, 'txt')

    def tipsa_create_shipping(self, picking):
        self.ensure_one()
        token_id = self.tipsa_authenticate()
        package_info = self._tipsa_prepare_create_shipping(picking, token_id)
        picking.write({
            'tipsa_last_request': fields.Datetime.now(),
        })
        res = self.tipsa_send(package_info)
        picking.write({
            'tipsa_last_response': fields.Datetime.now(),
        })
        tracking_reference_start = res.text.find('<v1:strGuidOut>{')
        tracking_reference_end = res.text.find('}</v1:strGuidOut>')
        if tracking_reference_start == -1 or tracking_reference_end == -1:
            raise exceptions.UserError(
                _('Tipsa: error creating shipping (tracking token): %s') % (
                    res.text))
        tracking_token = (
            res.text[tracking_reference_start + 16:tracking_reference_end])
        picking_tipsa_start = res.text.find('<v1:strAlbaranOut>')
        picking_tipsa_end = res.text.find('</v1:strAlbaranOut>')
        if picking_tipsa_start == -1 or picking_tipsa_end == -1:
            raise exceptions.UserError(
                _('Tipsa: error creating shipping (picking referenfe): %s') % (
                    res.text))
        picking.tipsa_picking_reference = (
            res.text[picking_tipsa_start + 18:picking_tipsa_end])
        picking.carrier_tracking_ref = '%s| %s%s%s' % (
            tracking_token, self.tipsa_agency_code, self.tipsa_agency_code,
            picking.tipsa_picking_reference)
        if res.status_code != 200:
            raise exceptions.UserError(
                _('Tipsa code error exception: %s, %s') % (
                    res.status_code, res.reason))
        self.get_label(picking, token_id)
        res = {
            'tracking_number': picking.carrier_tracking_ref,
            'exact_price': 0,
        }
        return res

    def tipsa_cancel_shipment(self, pickings):
        raise NotImplementedError(_('''
            Tipsa API doesn't provide methods to cancel picking,
            so you should relay on another price method instead or
            override this one in your custom code.
        '''))

    def tipsa_tracking_state_update(self, picking):
        raise NotImplementedError(_('''
            Tipsa API doesn't provide methods to update state,
            so you should relay on another price method instead or
            override this one in your custom code.
        '''))

    def tipsa_get_tracking_link(self, picking):
        raise NotImplementedError(_('''
            Tipsa API doesn't provide methods to update state,
            so you should relay on another price method instead or
            override this one in your custom code.
        '''))

    def tipsa_rate_shipment(self, order):
        raise NotImplementedError(_('''
            Tipsa API doesn't provide methods to compute delivery
            rates, so you should relay on another price method instead or
            override this one in your custom code.
        '''))
