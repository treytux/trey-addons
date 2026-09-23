###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2026-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Rental Availability Forecast',
    'summary': 'Rental availability validation and daily stock forecast',
    'category': 'Sales/Rental',
    'version': '16.0.1.3.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'rental_base',
        'sale_rental',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/rental_forecast_views.xml',
        'views/product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rental_availability_forecast/static/src/js/rental_forecasted.js',
            'rental_availability_forecast/static/'
            'src/xml/rental_forecasted.xml',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
}
