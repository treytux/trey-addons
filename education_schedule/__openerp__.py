# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2017-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Education Schedules',
    'summary': 'Education Schedules',
    'author': 'Trey Kilobytes de Soluciones (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Education',
    'version': '8.0.0.1.0',
    'depends': [
        'education',
    ],
    'data': [
        'reports/report_layout.xml',
        'reports/report_edu_schedule.xml',
        'security/ir.model.access.csv',
        'wizard/wizard_schedule.xml',
        'views/edu_period.xml',
        'views/edu_schedule.xml',
        'views/edu_time_slot.xml',
        'views/edu_training_plan.xml',
        'views/edu_training_plan_classroom.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
}
