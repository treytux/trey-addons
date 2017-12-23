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
    'name': 'Partner salesman create warehouse user',
    'category': 'Partner',
    'summary': 'Partner salesman create warehouse user.',
    'version': '8.0.0.1',
    'description': """
When a partner is marked as 'Is salesman' and is associated with a user, the
'Warehouse' user field becomes mandatory. You can select an existing one or
create one from the wizard 'Create warehouse'.
    """,
    'author': 'Trey (www.trey.es)',
    'depends': [
        'base',
        'partner_route',
        'stock',
    ],
    'data': [
        'wizard/wizard_create_warehouse.xml',
        'views/res_partner.xml',
        'views/res_users.xml',
    ],
    'installable': True,
}
