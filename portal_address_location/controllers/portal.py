###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class PortalAddressLocationCustomerPortal(CustomerPortal):
    OPTIONAL_BILLING_FIELDS = CustomerPortal.OPTIONAL_BILLING_FIELDS + [
        'zip_id',
    ]

    def details_form_validate(self, data, partner_creation=False):
        location = False
        location_id = data.get('zip_id')
        if location_id:
            try:
                location = request.env['res.city.zip'].sudo().browse(
                    int(location_id)).exists()
            except (TypeError, ValueError):
                location = False
            if not location:
                data['zip_id'] = False
                error, error_message = super().details_form_validate(
                    data, partner_creation=partner_creation)
                error['zip_id'] = 'error'
                error_message.append(_('The selected location is invalid.'))
                return error, error_message
            location = location[0]
            data['zip_id'] = location.id
            data['city'] = location.city_id.name
            data['zipcode'] = location.name
            data['country_id'] = str(location.country_id.id)
            data['state_id'] = str(location.state_id.id or '')
        return super().details_form_validate(
            data, partner_creation=partner_creation)
