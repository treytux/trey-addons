###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2026-Today Trey, Kilobytes de Soluciones <www.trey.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Account analytic line project wizard',
    'version': '16.0.1.1.0',
    'license': 'AGPL-3',
    'category': 'Invoicing',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'depends': [
        'account',
        'analytic',
        'hr_expense',
        'project',
        'sale',
        'sale_timesheet',
        'hr_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_analytic_line_views.xml',
        'wizards/analytic_create_invoice_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
