# Copyright 2019 Vicent Cubells - Trey <http://www.trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Purchase Order Cumulative Discount",
    'summary': "Express discounts on PO lines as mathematical expressions",
    'author': 'Trey (www.trey.es), Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/purchase-workflow',
    'category': 'Purchase Management',
    'license': 'AGPL-3',
    'version': '12.0.1.1.3',
    'depends': [
        'account_invoice_cumulative_discount',
        'purchase_discount',
    ],
    'data': [
        'views/purchase_order_views.xml',
        'views/res_partner_views.xml',
        'views/product_supplierinfo_views.xml',
        'reports/report_purchaseorder.xml',
    ]
}
