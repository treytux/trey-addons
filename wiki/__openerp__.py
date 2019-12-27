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
    'name': 'wiki',
    'category': 'Tools',
    'summary': 'Wiki',
    'version': '8.0.0.1',
    'description': '''
Wiki to insert content. Allows users belonging to the group 'Employee' to
register entries and search by title, tags and description.

This module depends OCA module web_widget_text_markdown you can found at:
https://github.com/OCA/web/tree/8.0
''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'mail',
        'web_widget_text_markdown'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/wiki_view.xml',
        'views/wiki_tag_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
}
