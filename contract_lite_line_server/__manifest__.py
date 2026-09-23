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
    'name': 'Contract Lite Line Server',
    'summary': 'Managed server data for contract lite lines',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Sales',
    'version': '16.0.1.1.1',
    'depends': [
        'contract_lite',
        'product',
        'sales_team',
    ],
    'data': [
        'data/mail_template_data.xml',
        'security/ir.model.access.csv',
        'views/contract_lite_contract_views.xml',
        'views/contract_lite_line_views.xml',
        'views/product_template_views.xml',
        'wizards/contract_lite_line_server_occupation_import_wizard.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
}
