# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Security Portal',
    'category': 'Portal',
    'summary': 'Generate group users for Portal',
    'version': '8.0.0.1',
    'description': 'Generate group users for Portal',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'base',
        'portal',
        'portal_project',
        'portal_claim',
        'portal_project_issue',
        'mail',
    ],
    'data': [
        'security/portal_security.xml',
        'security/ir.model.access.csv',
        'views/portal_view.xml',
        'data/portal_data.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'application': False,
}
