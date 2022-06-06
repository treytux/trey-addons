###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website RMA',
    'category': 'Website',
    'summary': 'Return Merchandise Authorizations for website',
    'version': '12.0.1.10.0',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'portal',
        'product',
        'sale',
        'sale_return',
        'website_sale',
    ],
    'data': [
        'data/report_paperformat.xml',
        'data/website_rma_email.xml',
        'reports/address_label_report.xml',
        'views/portal_template.xml',
        'views/sale_portal_template.xml',
        'views/website_rma_template.xml',
        'views/website_template.xml',
    ],
    'installable': True
}
