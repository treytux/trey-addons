# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _
import json


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_sii_taxes_map(self, codes):
        self.ensure_one()
        if self.company_id.state_id.code in ['35', '38']:
            taxes = self.env['account.tax']
            sii_map = self.env['aeat.sii.map'].search([
                ('state_id', '=', self.company_id.state_id.id),
                '|',
                ('date_from', '<=', self.date_invoice),
                ('date_from', '=', False),
                '|',
                ('date_to', '>=', self.date_invoice),
                ('date_to', '=', False)], limit=1)
            if not sii_map:
                raise exceptions.Warning(_(
                    'SII Map not found. Check your configuration.'))
            mapping_taxes = {}
            tax_templates = sii_map.sudo().map_lines.filtered(
                lambda x: x.code in codes
            ).taxes
            for tax_template in tax_templates:
                taxes += self.map_sii_tax_template(tax_template, mapping_taxes)
            return taxes
        else:
            return super(AccountInvoice, self)._get_sii_taxes_map(codes)

    @api.multi
    def _connect_sii(self, wsdl):
        if self.company_id.sii_test:
            raise exceptions.Warning(_(
                'Currently, there is no valid testing environment for the '
                'Canary Islands SII. You must deactivate the option \'Is Test '
                'Environment? \' from the \'Configuration\' tab of the '
                'company for the invoice send in real environment.'))
        return super(AccountInvoice, self)._connect_sii(wsdl)

    def _iva_to_igic(self, dict):
        if self.company_id.state_id.code in ['35', '38']:
            dict = json.loads(json.dumps(dict).replace(
                'DetalleIVA', 'DetalleIGIC'))
            dict = json.loads(json.dumps(dict).replace(
                'DesgloseIVA', 'DesgloseIGIC'))
            dict = json.loads(json.dumps(dict).replace(
                'ImporteTransmisionInmueblesSujetoAIVA',
                'ImporteTransmisionInmueblesSujetoAIGIC'))
            dict = json.loads(json.dumps(dict).replace(
                'PeriodoImpositivo', 'PeriodoLiquidacion'))
        return dict

    @api.multi
    def _get_sii_invoice_dict_out(self, cancel=False):
        res = super(AccountInvoice, self)._get_sii_invoice_dict_out(
            cancel=cancel)
        res = self._iva_to_igic(res)
        return res

    @api.multi
    def _get_sii_invoice_dict_in(self, cancel=False):
        res = super(AccountInvoice, self)._get_sii_invoice_dict_in(
            cancel=cancel)
        res = self._iva_to_igic(res)
        # Compras comerciante minorista
        if (self.company_id.state_id.code in ['35', '38'] and
                self.sii_registration_key.code == '15' and
                self.sii_registration_key.type == 'purchase'):
            detalle_IGIC = res['FacturaRecibida']['DesgloseFactura'][
                'DesgloseIGIC']['DetalleIGIC']
            for r in detalle_IGIC:
                r.pop('CuotaSoportada')
        return res

    @api.multi
    def _get_sii_header(self, tipo_comunicacion=False, cancellation=False):
        header = super(AccountInvoice, self)._get_sii_header(
            tipo_comunicacion=tipo_comunicacion, cancellation=cancellation)
        header["IDVersionSii"] = 1.0
        return header
