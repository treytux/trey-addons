# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _connect_sii(self, wsdl):
        company = self.env.user.company_id
        if company.sii_test and company.state_id.code == '20':
            if 'FactEmitidas' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/fe/SiiFactFEV1SOAP')
            elif 'FactRecibidas' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/fr/SiiFactFRV1SOAP')
            elif 'BienesInversion' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/bi/SiiFactBIV1SOAP')
            elif 'OpIntracomunitarias' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/oi/SiiFactOIV1SOAP')
            elif 'CobrosEmitidas' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/fe/SiiFactCOBV1SOAP')
            elif 'PagosRecibidas' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/fr/SiiFactPAGV1SOAP')
            elif 'OpTrascendTribu' in wsdl:
                wsdl = (u'https://sii-prep.egoitza.gipuzkoa.eus/JBS/HACI/SSII-'
                        'FACT/ws/pm/SiiFactCMV1SOAP')
            else:
                raise exceptions.Warning(_('Wsdl not found to test mode!'))
        return super(AccountInvoice, self)._connect_sii(wsdl)
