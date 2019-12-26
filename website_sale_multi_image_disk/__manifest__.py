###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Website Sale Multi Image Disk',
    'category': 'e-commerce',
    'summary': 'Allow to read product images from disk',
    'version': '11.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'depends': ['website_sale'],
    'data': [
        'views/product_attribute_view.xml',
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'views/res_config_settings_view.xml'
    ],
    'installable': True,
}
