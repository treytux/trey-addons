# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Sale Order Cumulative Discount",
    'summary': "Express discounts on SO lines as mathematical expressions",
    'author': 'Onestein, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/sale-workflow',
    'category': 'Sales',
    'license': 'AGPL-3',
    'version': '12.0.1.1.2',
    'depends': [
        'account_invoice_cumulative_discount',
        'sale',
    ],
    'data': [
        'views/sale_order_views.xml',
        'reports/sale_report_templates.xml',
    ]
}
