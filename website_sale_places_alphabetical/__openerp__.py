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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
###############################################################################

{
    'name': 'Places by alphabetical order [deprecated]',
    'category': 'website',
    'summary': 'Ordena alfabéticamente países y estados o provincias del '
               'checkout.',
    'version': '8.0.0.1',
    'description': """
Ordena alfabéticamente los selectores de países y estados o provincias del
checkout teniendo en cuenta su traducción.
Por cuestiones de rendimiento, Odoo no implementa dicha ordenación a nivel de
servidor, por lo que se ofrece esta solución alternativa que se ejecuta en el
cliente.
""",
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/website.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
}
