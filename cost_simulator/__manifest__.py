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
    'name': 'Costs Simulator',
    'version': '12.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Custom Modules',
    'description': """Cost Proyect Simulator""",
    'depends': [
        'account_payment_mode',
        'account_payment_partner',
        'analytic',
        'hr_expense',
        'procurement_jit',
        'project',
        'project_task_code',
        'purchase',
        'sale_order_type',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cost_simulator_sequence.xml',
        'wizards/wizard_history_pricelist_views.xml',
        'wizards/wizard_simulation_accepted_views.xml',
        'views/simulation_cost_views.xml',
        'views/simulation_cost_history_views.xml',
        'views/simulation_cost_history_line_views.xml',
        'views/res_company_views.xml',
        'views/chapter_templates.xml',
    ],
}
