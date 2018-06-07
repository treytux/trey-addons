# -*- coding: utf-8 -*-
# © 2015 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Fleet Current Vehicule',
    'summary': 'Current vehicle by user',
    'version': '8.0.1.0.0',
    'category': 'Managing vehicles and contracts',
    'website': 'https://www.trey.es',
    'author': 'Trey (www.trey.es)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'fleet',
    ],
    'data': [
        'views/user_view.xml'
    ]
}
