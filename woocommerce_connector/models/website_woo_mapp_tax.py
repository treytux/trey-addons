###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WebsiteWooMappTax(models.Model):
    _name = 'website.woo.mapp.tax'
    _inherit = ['website.woo.mixin']
    _description = 'Website Woocommerce Mapp Tax'

    website_id = fields.Many2one(
        comodel_name='website',
        string='Website',
        required=True,
    )
    name = fields.Char(
        string='Name in Woo',
        required=True,
    )
    woo_id = fields.Integer(
        string='Id in Woo',
    )
    woo_rate = fields.Float(
        string='Rate',
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax in Odoo',
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position',
    )
    intracommunity_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax in Odoo',
    )
    intracommunity_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position',
    )

    def woo_endpoint_get(self, woo_id=None):
        endpoint = 'taxes'
        if woo_id:
            endpoint = '%s/%s' % (endpoint, woo_id)
        return endpoint

    def woo_sync_import_record(self, website, data):
        tax_data = {
            'website_id': website.id,
            'woo_id': data['id'],
            'name': data['name'],
            'woo_rate': data['rate'],
        }
        tax = self.search([
            ('website_id', '=', website.id),
            ('woo_id', '=', data['id']),
        ])
        if tax:
            tax.write(tax_data)
            return False
        return self.create(tax_data)
