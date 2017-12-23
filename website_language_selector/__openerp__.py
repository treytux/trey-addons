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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Language Selector',
    'category': 'website',
    'summary': 'Allow to choose language from website menu',
    'version': '8.0.1.0.0',
    'description': '''
Website Language Selector
=========================
Add language selector to the website main menu.
''',
    'author': (
        'Trey (wwww.trey.es), '
        'Muharrem Senyil '
        '(Flat Flags: https://dribbble.com/shots/1211759-free-195-flat-flags)'
    ),
    'depends': [
        'website',
    ],
    'data': [
        'templates/website.xml',
        'templates/website_language_selector.xml',
    ],
    'installable': True,
}
