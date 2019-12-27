# -*- coding: utf-8 -*-
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Print Formats Base',
    'category': 'Tools',
    'summary': 'Base print formats',
    'version': '8.0.0.1',
    'description': """
Personalización en Configuración de la Compañía

Asignar Logotipo:
720x320 pixels a 300ppp

Asignar a Encabezado RML: Nombre Empresa, S.L.<br/>Nombre de la calle, 1<br/>
99999 Ciudad (Provincia)<br/>www.dominio.es

Activar Pie de página personalizado y asignar a Pie de página del informe: 999
99 99 99 - info@dominio.es - www.dominio.es<br/><br/>
    """,
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'website': 'https://www.trey.es',
    'depends': [
        'report',
    ],
    'data': [
        'data/report_paperformat.xml',
        'report/report_layout.xml',
        'views/res_company_view.xml',
    ],
    'installable': True,
}
