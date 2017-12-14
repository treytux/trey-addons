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
    'name': 'Eliminar referencias a odoo',
    'category': 'Base',
    'summary': 'Modulo Base',
    'version': '8.0.0.1',
    'description': """
Este modulo elimina las referencias a Odoo de la aplicación.

Compatible con la version OpenERP 7, OpenERP 8 trunk y Odoo master
        """,
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'depends': ['base', 'base_setup', 'auth_signup', 'mail', 'web'],
    'data': [
        'static/src/xml/backoffice.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
        'static/src/xml/announcement.xml',
    ],
    'js': [
    ],
    'css': [
    ],
    'installable': True,
}
