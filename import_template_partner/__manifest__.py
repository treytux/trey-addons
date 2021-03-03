###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Import template partner',
    'summary': 'Import partner data from files Excel or CSV from templates',
    'category': 'Tools',
    'version': '12.0.1.0.0',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'account_credit_control',
        'account_payment_partner',
        'base',
        'base_location',
        'import_template',
        'l10n_es_partner',
        'product_pricelist_purchase',
        'purchase_discount',
        'sale_commission',
        'sale_invoice_group_method',
    ],
    'data': [
        'data/data.xml',
    ],
}
