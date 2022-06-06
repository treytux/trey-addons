##############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2022-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'TicketBAI - Invoice refund link',
    'version': '12.0.1.0.0',
    'summary': 'Relate refund invoice to the original invoice',
    'license': 'AGPL-3',
    'author': 'Trey (www.trey.es)',
    'website': 'https://www.trey.es',
    'category': 'Accounting & Finance',
    'depends': [
        'account_invoice_link_refund',
        'account_invoice_refund_link',
        'l10n_es',
        'l10n_es_aeat',
        'l10n_es_ticketbai',
        'sale',
    ],
}
