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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Website URL Friendly [DEPRECATED]',
    'version': '8.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Website',
    'summary': 'Deprecated: use website_seo_url',
    'description': '''
Website URL Friendly
====================
Add custom urls in the website. Add in 'Promote' section of website slug
management that allow to customize urls.
''',
    'license': 'GPL-3',
    'depends': [
        'base',
        'website',
    ],
    'data': [
        'views/slug_view.xml',
        'views/website_templates.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': ['static/src/xml/website.seo.xml'],
    'demo': [],
    'auto_install': False,
    'installable': True,
    'images': [],
}
