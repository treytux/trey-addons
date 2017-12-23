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
    'name': 'Project Task Invoice',
    'category': 'project',
    'summary': 'Invoice a task and project',
    'version': '8.0.0.1',
    'description': '''
    This module depends:
        - stock_picking_sales_type
    ''',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'account',
        'stock_account',
        'project',
        'project_task_sheet_product',
        'project_task_stock_moves',
        'project_timesheet',
        'stock_account_extend',
        'stock_picking_sales_type'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task_view.xml',
        'views/account_invoice_view.xml',
        'wizards/create_invoice.xml'
    ],
    'installable': True,
}
