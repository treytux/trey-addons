###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2018-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Vertical Base',
    'summary': 'Dependencies addons for base instance',
    'category': 'Vertical',
    'version': '12.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        # Los modulos comentados es por que están pendientes de migracion
        # 'database_cleanup',
        'mass_editing',
        'web_dialog_size',
        'web_export_view',
        'mail_debrand',
        # 'web_group_expand',
        'web_decimal_numpad_dot',
        'web_search_with_and',
        'web_no_bubble',
        'web_searchbar_full_width',
        'web_responsive',
        'web_tree_resize_column',
        'web_tree_many2one_clickable',
        'website_odoo_debranding'
    ],
    'application': True,
    'installable': True,
}
