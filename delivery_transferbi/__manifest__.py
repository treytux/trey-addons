# Copyright 2020 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Delivery TRANSFERBI',
    'summary': 'Integrate TRANSFERBI webservice',
    'author': 'Trey (www.trey.es), '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'category': 'Delivery',
    'version': '12.0.1.5.0',
    'depends': [
        'delivery',
        'delivery_package_number',
        'delivery_price_method',
        'delivery_state',
        'print_formats_delivery_label',
    ],
    'external_dependencies': {
        'python': ['zeep'],
    },
    'data': [
        'views/delivery_carrier_views.xml',
        'views/report_print_formats_delivery_label.xml',
    ],
}
