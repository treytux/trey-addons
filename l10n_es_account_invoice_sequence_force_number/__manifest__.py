###############################################################################
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http: //www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'l10n es account invoice sequence force number',
    'summary': '''
Makes the "account_invoice_force_number" module compatible when the Spanish
localization module "l10n_es_account_invoice_sequence" is installed.''',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'category': 'Invoice',
    'version': '12.0.1.0.0',
    'depends': [
        'account_invoice_force_number',
        'l10n_es_account_invoice_sequence',
    ],
    'images': [
        'static/description/banner.png',
    ],
}
