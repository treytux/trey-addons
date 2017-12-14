# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.http import request


class WebsiteSale(website_sale):
    def checkout_parse(self, address_type, data, remove_prefix=False):
        res = super(WebsiteSale, self).checkout_parse(
            address_type=address_type, data=data, remove_prefix=remove_prefix)
        if (not isinstance(data, dict) and address_type == 'billing' and
                data.root_partner_id.is_company):
            res['street2'] = data.street
            res['street'] = data.root_partner_id.name
        return res

    def show_form(self, checkout, type):
        form_data = self.checkout_form_validate(checkout)
        form_data.pop('street2', None)
        form_data.pop('email', None)
        return form_data == {} and 1 or 0
        # if form_data == {}:
        #     return 1
        # return 0

    def checkout_values(self, data=None):
        res = super(WebsiteSale, self).checkout_values(data=data)
        if data:
            res['checkout'].update(self.checkout_parse('shipping', data))
        orm_user = request.env['res.users']
        partner = orm_user.sudo().browse(request.uid).partner_id
        if not partner:
            return res
        if 'checkout' not in res:
            res['checkout'] = {}
        res['checkout']['address_id'] = partner.id
        res['checkout']['is_company'] = partner.root_partner_id.is_company
        if partner.country_id:
            res['checkout']['country_name'] = partner.country_id.name
        if partner.state_id:
            res['checkout']['state_name'] = partner.state_id.name
        res['checkout']['show_form'] = self.show_form(
            res['checkout'], 'checkout')
        res['checkout']['show_form_shipping'] = self.show_form(
            self.checkout_parse('shipping', res['checkout'], True), 'shipping')
        return res

    def checkout_form_save(self, checkout):
        checkout.pop('country_name', None)
        checkout.pop('state_name', None)
        if checkout.get('is_company', None):
            company_name = checkout.get('street', None)
            checkout['street'] = checkout.get('street2', None)
            checkout.pop('street2')
        billing_address = self.checkout_parse('billing', checkout, True)
        data_billing = {}
        order = request.website.sale_get_order()
        if 'vat' in billing_address:
            data_billing.update({'vat': billing_address.get('vat', None)})
        if checkout.get('is_company', None):
            data_billing.update({'name': company_name, 'vat': None})
            order.partner_id.root_partner_id.write(data_billing)
        if data_billing != {}:
            order.partner_id.write(data_billing)
        res = super(WebsiteSale, self).checkout_form_save(checkout)
        ship_id = checkout.get('shipping_id')
        if ship_id != 0 or ship_id == -1:
            data = {}
            data.update(self.checkout_parse('shipping', checkout))
            for checkout_name in data.keys():
                field_name = str(checkout_name).split('_', 1)[1]
                data[field_name] = checkout[checkout_name]
                data.pop(checkout_name)
            order.partner_shipping_id.write(data)
        return res

    def checkout_form_validate(self, data):
        error = super(WebsiteSale, self).checkout_form_validate(data)
        env = request.env
        address_id = data.get('address_id', None)
        vat = data.get('vat', None)
        if data.get('shipping_id') != 0:
            for field_name in self._get_mandatory_shipping_fields():
                field_name = 'shipping_' + field_name
                if not data.get(field_name):
                    error[field_name] = 'missing'
        if address_id and vat:
            address = env['res.partner'].sudo().browse(address_id)
            if address and address.vat == vat:
                return error
            partner = env['res.partner'].sudo().search(
                [('vat', '=', vat)], limit=1)
            if len(partner) > 0 and partner.id != env.user.partner_id.id:
                error['vat'] = 'The VAT %s already exists' % vat
        return error
