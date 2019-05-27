# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
{
    'name': 'Res partner comercial fix',
    'summary': 'Res partner comercial fix',
    'description': '''
When a trade name is assigned to a partner and the field is later modified or
deleted, the field 'display_name' is not recalculated, so the old trade name
is still shown in parentheses before of the partner name.

This module fixs this fault so that when the trade name is modified or
deleted, 'display_name' field will be recalculed to update its value.

A script is added to run in odoo shell to recalculate the field 'display_name'
for all the partners that are already created in the database.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Customer Relationship Management',
    'version': '8.0.0.1.0',
    'depends': ['l10n_es_partner'],
    'data': [],
    'installable': True,
}
