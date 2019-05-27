###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

import logging
_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    import_code = fields.Char(
        string='Code for import',
        copy=False)

    @api.multi
    @api.constrains('import_code')
    def _check_rule_ids(self):
        for pricelist in self:
            pl = self.search([
                ('import_code', '=', pricelist.import_code),
                ('id', '!=', pricelist.id)])
            if pl:
                raise ValidationError(
                    _('Code %s already exists for pricelist "%s"') % (
                        pricelist.import_code, pl.name))

    @api.model
    def import_excel(self, fname):
        df = pd.read_excel(
            fname, engine='xlrd', encoding='utf-8', na_values=['NULL'])
        if 'default_code' not in df.columns:
            raise UserError(_('Column "default_code" not exists'))
        pricelists = {}
        for col in [c for c in df.columns if c != 'default_code']:
            if 'Unnamed:' in col:
                continue
            if col in ['list_price', 'standard_price']:
                pricelists[col] = None
                continue
            pl = self.search([('import_code', '=', col)], limit=1)
            if not pl:
                raise UserError(
                    _('Column "%s" does not match any price list') % col)
            pricelists[col] = pl
        for index, row in df.iterrows():
            product_tmpl = self.env['product.template'].search(
                [('default_code', '=', row['default_code'])])
            if not product_tmpl:
                raise UserError(
                    _('Default code product "%s" not exists') %
                    row['default_code'])
            if len(product_tmpl) > 1:
                raise UserError(
                    _('Default code "%s" return more that one product') %
                    row['default_code'])
            for col, pricelist in pricelists.items():
                if not row[col] or pd.isnull(row[col]):
                    continue
                try:
                    value = float(row[col])
                except ValueError:
                    raise UserError(
                        _('Value for column "%s" in row %s isn\'t a number') %
                        (col, index + 1))
                if col == 'list_price':
                    product_tmpl.list_price = value
                    continue
                elif col == 'standard_price':
                    product_tmpl.standard_price = value
                    continue
                items = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', product_tmpl.id)])
                if items:
                    items.write({'fixed_price': value})
                else:
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': pricelist.id,
                        'product_tmpl_id': product_tmpl.id,
                        'applied_on': '1_product',
                        'min_quantity': 1,
                        'compute_price': 'fixed',
                        'fixed_price': value})
