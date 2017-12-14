# -*- coding: utf-8 -*-
##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2014-Today Trey, Kilobytes de Soluciones
#    (<http://https://www.trey.es>).
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
    "name": "Register and reset password",
    "version": '8.0.0.1',
    "author": 'Trey Kilobytes de Soluciones (https://www.trey.es)',
    'website': "https://www.trey.es",
    "category": "Website",
    "description": """
Crea un usuario en Odoo tras chequear que un email ya pertenece a un cliente o
contacto y le envía un mail para resetear la contraseña.
""",
    "license":  "AGPL-3",
    "depends": [
        "auth_signup"
    ],
    "data": [],
    "demo": [],
    'auto_install': False,
    "installable": True
}
