###############################################################################
#
#    Trey, Kilobytes de Soluciones
#    Copyright (C) 2019-Today Trey, Kilobytes de Soluciones <www.trey.es>
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
    'name': 'Vertical Website',
    'category': 'Vertical',
    'summary': 'Addons dependencies for Website',
    'version': '12.0.1.5.0',
    'website': 'https://www.trey.es',
    'license': 'AGPL-3',
    'author': 'Trey (www.trey.es)',
    'depends': [
        'website',
        'website_canonical_url',
        'website_crm_privacy_policy',
        'website_fix_protocol_language_links',
        'website_fix_protocol_metas',
        'website_logo',
        'website_protocol',
        'website_reset_styles',
        'website_schema_org',
    ],
    'data': [
        'views/website_templates.xml',
    ],
    'application': True,
}
