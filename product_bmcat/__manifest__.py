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
    'name': 'Product BMEcat Export',
    'summary': 'Export product catalog to BMEcat XML format',
    'category': 'Product',
    'version': '16.0.1.1.1',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'product_catalog_label',
        'product',
        'sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_catalog_views.xml',
        'views/export_bmcat_wizard_views.xml',
    ],
    'external_dependencies': {
        'python': [],
    },
    'images': [
        'static/description/banner.png',
    ],
}
