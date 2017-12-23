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
    'name': 'Website Snippets',
    'summary': 'Bloques de contenido compatibles con Bootstrap '
               'para arrastrar y soltar',
    'description': """
    """,
    'version': '8.0.0.1',
    'author': 'Trey (www.trey.es)',
    'category': 'website',
    'depends': [
        'website',
        'website_breadcrumb',
        'website_less',
    ],
    'data': [
        'templates/snippets.xml',
        'templates/website.xml',
        'templates/website_less.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
}
