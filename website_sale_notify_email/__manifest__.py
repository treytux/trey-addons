###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2024-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
#    along with this program. If not, see <http: //www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website Sale Notify Email',
    'summary': 'Send a notificacion Email when a sale is created on website',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Project',
    'version': '12.0.1.1.2',
    'depends': [
        'mail',
        'website_sale',
    ],
    'data': [
        'views/website_views.xml',
        'data/mail_template_data.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
