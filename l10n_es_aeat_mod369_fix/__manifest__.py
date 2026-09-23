##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2023-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'l10n_es_aeat_mod369_fix',
    'summary': 'Fix empy records in 369 model file',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'version': '12.0.1.0.0',
    'depends': [
        'l10n_es_aeat_mod369',
    ],
    'data': [
        'data/l10n_es_aeat_mod369/04/aeat.model.export.config.line.csv',
        'data/l10n_es_aeat_mod369/05/aeat.model.export.config.line.csv',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
