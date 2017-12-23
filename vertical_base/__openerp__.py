# -*- coding: utf-8 -*-
###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2016-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'category': 'Vertical',
    'summary': 'Dependencies addons for base instance',
    'version': '8.0.1.0.0',
    'description': '',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'database_cleanup',
        'disable_openerp_online',
        'mass_editing',
        'support_branding',
        'warning',
        'web',
        'web_styles_fix',
        'web_dialog_size',
        'web_export_view',
        'web_group_expand',
        'web_search_with_and',
        'web_searchbar_full_width',
        'web_sheet_full_width',
        'web_tree_many2one_clickable',
        'web_widget_float_formula',
    ],
    'data': [
        'data/ir_config_parameter.xml'
    ],
    'application': True,
    'installable': True,
}
