###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.tools.misc import formatLang


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    website_description = fields.Text(
        string='Website description',
        compute='_compute_website_description')

    @api.model
    def format_date(self, date, date_format, prefix='', suffix=''):
        return date and ''.join((prefix, fields.Datetime.from_string(
            date).strftime(date_format), suffix)) or ''

    @api.multi
    def _get_date_description(self, date, lang, text):
        self.ensure_one()
        return '%s' % (
            self.format_date(self.date_start, lang.date_format, text))

    @api.multi
    def _get_min_quantity_description(self, lang):
        self.ensure_one()
        if not self.min_quantity or self.min_quantity <= 1:
            return ''
        if self.applied_on not in ['1_product', '0_product_variant']:
            return ''
        product = (
            self.applied_on == '1_product' and self.product_tmpl_id or
            self.product_id)
        product = product.with_context(quantity=self.min_quantity)
        return _(
            'Buying %s units the price will be %s') % (
            self.min_quantity,
            formatLang(
                self.env, self.pricelist_id.currency_id.round(
                    product.website_price / self.min_quantity),
                currency_obj=self.pricelist_id.currency_id))

    @api.multi
    def _get_compute_price_description(self, lang):
        self.ensure_one()
        if self.compute_price == 'fixed':
            return _('Fixed price %s') % formatLang(
                self.env, self.fixed_price,
                currency_obj=self.pricelist_id.currency_id)
        elif self.compute_price == 'percentage':
            return _('Get %s%% of discount') % round(self.percent_price)
        else:
            return _('Obtain a great discount')

    @api.multi
    def _get_applied_on_messages(self):
        self.ensure_one()
        return {
            '3_global': _('In all our products'),
            '2_product_category':
                _('For products in %s category') % self.categ_id.name,
            '1_product': _('In all variants of this product'),
            '0_product_variant':
                _('For the variant %s of this product')
                % self.product_id.name}

    @api.one
    @api.depends(
        'date_start', 'date_end', 'min_quantity', 'compute_price',
        'fixed_price', 'percent_price')
    def _compute_website_description(self):
        lang = self.env['res.lang']._lang_get(self.env.user.lang)
        applied_messages = self._get_applied_on_messages()
        self.website_description = '\n'.join([description for description in [
            self._get_min_quantity_description(lang),
            self._get_compute_price_description(lang),
            self.applied_on and applied_messages[self.applied_on] or ''] if
            description != ''])
