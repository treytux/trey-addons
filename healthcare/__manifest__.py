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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Healthcare',
    'summary': 'Healthcare management',
    'version': '16.0.1.3.0',
    'category': 'Healthcare',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'partner_interest_group',
        'partner_multi_relation',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_partner_views.xml',
        'views/partner_protected_data_views.xml',
        'views/partner_info_data_views.xml',
        'views/partner_protected_document_views.xml',
        'views/partner_protected_document_category_views.xml',
        'views/partner_history_views.xml',
        'views/partner_history_type_views.xml',
        'views/partner_risk_views.xml',
        'views/menu.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
