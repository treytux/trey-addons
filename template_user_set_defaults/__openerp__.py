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
    'name': 'Template User Defaults',
    'category': 'website',
    'summary': 'Asignar valores por defecto a los nuevos usuarios.',
    'version': '8.0.0.1',
    'description': '''
    A partir del usuario asignado como Template User, se toman todos los
    valores por defecto para los nuevos usuarios creados en la tienda online:
    Posición Fiscal, Plazo de pago del cliente, ...
    ''',
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'depends': [
        'auth_signup',
        'account',
        'website_sale'
    ],
    'installable': True,
}
