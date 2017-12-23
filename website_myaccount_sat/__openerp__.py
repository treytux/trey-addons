# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2015-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'My Account SAT',
    'category': 'website',
    'summary': 'Manage claims documents in the frontend portal',
    'description': """
    Lista de reclamaciones pertenecientes a un técnico.
    """,
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'version': '8.0.1.0.0',
    'depends': [
        'base',
        'crm',
        'crm_claim',
        'crm_claim_product_sold',
        'crm_claim_sat',
        'crm_claim_extend',
        'mail',
        'print_formats_claim',
        'root_partner',
        'website_myaccount',
    ],
    'data': [
        'security/claim_security.xml',
        'security/ir.model.access.csv',
        'data/data_users.xml',
        'templates/website.xml',
        'templates/website_myaccount.xml',
        'templates/website_myaccount_sat.xml',
    ],
    'installable': True,
}
