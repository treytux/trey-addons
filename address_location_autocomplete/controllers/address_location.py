###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class AddressLocationAutocompleteController(http.Controller):

    @http.route(
        '/address_location_autocomplete/search',
        type='json', auth='public', website=True)
    def address_location_autocomplete_search(
            self, search='', country_id=None, **kw):
        search = str(search or '').strip()
        if len(search) < 2:
            return []
        domain = [
            '|',
            ('name', 'ilike', search),
            ('city_id.name', 'ilike', search),
        ]
        try:
            country_id = int(country_id) if country_id else False
        except (TypeError, ValueError):
            country_id = False
        if country_id:
            domain.append(('country_id', '=', country_id))
        locations = request.env['res.city.zip'].sudo().search(
            domain, order='name, city_id', limit=20)
        return [{
            'id': location.id,
            'label': location.display_name,
            'zip': location.name,
            'city': location.city_id.name,
            'city_id': location.city_id.id,
            'state_id': location.state_id.id,
            'state': location.state_id.name,
            'country_id': location.country_id.id,
            'country': location.country_id.name,
        } for location in locations]
