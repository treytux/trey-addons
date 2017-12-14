# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_partner(self, partner_data):
        '''Create a partner with data dictionary given as a parameter.'''
        try:
            if 'vat' in partner_data:
                if partner_data['vat'] == '':
                    del partner_data['vat']
                else:
                    partner_data['vat'] = partner_data['vat'].upper()
                    vat_country, vat_number = (
                        partner_data['vat'][:2].lower(),
                        partner_data['vat'][2:].replace(' ', ''))
                    vat_ok = self.env['res.partner'].simple_vat_check(
                        vat_country, vat_number)
                    if not vat_ok:
                        _log.error('NIF %s incorrecto: %s, %s' % (
                            partner_data['vat'], vat_country, vat_number))
                        raise Exception(
                            'NIF %s incorrecto' % partner_data['vat'])
            partner = self.env['res.partner'].create(partner_data)
            return {'partner_id': partner.id}
        except Exception as e:
            _log.error(e)
            return {'errors': [{'name': 'ValidateError', 'value': e.message}]}

    @api.model
    def write_partner(self, partner_data):
        '''Update partner with data in dictionary given as parameter.'''
        try:
            if 'vat' in partner_data:
                if partner_data['vat'] == '':
                    del partner_data['vat']
                else:
                    partner_data['vat'] = partner_data['vat'].upper()
                    vat_country, vat_number = (
                        partner_data['vat'][:2].lower(),
                        partner_data['vat'][2:].replace(' ', ''))
                    vat_ok = self.env['res.partner'].simple_vat_check(
                        vat_country, vat_number)
                    if not vat_ok:
                        _log.error('NIF %s incorrecto: %s, %s' % (
                            partner_data['vat'], vat_country, vat_number))
                        raise Exception(
                            'NIF %s incorrecto' % partner_data['vat'])
            if 'id' not in partner_data:
                return {'errors': [{
                    'name': 'Id obligatorio',
                    'value': 'El campo Id es obligatorio'}]}
            partner_id = partner_data['id']
            del partner_data['id']
            partner = self.env['res.partner'].browse(partner_id)
            if partner:
                partner.write(partner_data)
                return {'partner_id': partner.id}
            else:
                return {'errors': [{
                    'name': 'Partner no existe',
                    'value': 'El partner con id %s no existe' % (
                        partner_data['id'])}]}
        except Exception as e:
            _log.error(e)
            return {'errors': [{'name': 'ValidateError', 'value': e.message}]}
