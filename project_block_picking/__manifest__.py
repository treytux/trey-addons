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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Project block picking',
    'summary': 'Block stock moves on pickings of blocked or closed tasks',
    'description': '''
        Prevents adding or editing stock moves on a picking when its linked
        task is blocked (kanban state) or when the task's project blocks
        pickings, is archived or is in a folded (closed) stage.''',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'category': 'Project',
    'version': '16.0.1.0.2',
    'depends': [
        'project',
        'stock',
    ],
    'data': [
        'views/project_project_view.xml',
        'views/stock_picking_view.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
}
