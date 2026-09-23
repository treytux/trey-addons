###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    code_suffix = fields.Char(
        string='Sufix',
    )
    default_code = fields.Char(
        copy=False,
    )
    default_code_copy = fields.Char(
        string='Default Code',
        related='default_code',
        readonly=True,
    )

    @api.constrains('default_code', 'code_suffix')
    def _check_default_code(self):
        if self.default_code:
            product = self.search([
                ('id', '!=', self.id),
                ('code_suffix', '=', self.code_suffix),
                ('default_code', '=', self.default_code),
            ], limit=1)
            if product:
                raise ValidationError(_(
                    'Error! The default code %s already exists.' %
                    self.default_code))

    def _get_default_code_seq_type(self, seq_type=None):
        self.ensure_one()
        seq_type = seq_type and seq_type or self.code_seq_type or '?'
        return '%s-%s%s%s' % (
            seq_type, self.categ_id.code_seq or 'XX', str(self.id).zfill(5),
            self.code_suffix and '-%s' % self.code_suffix or '')

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        for vals in vals_list:
            for product in products:
                assign_default_code = (
                    ('product_tmpl_id' in vals or product.product_tmpl_id)
                    and 'default_code' not in vals
                )
                if assign_default_code:
                    product.default_code = product._get_default_code_seq_type()
        return product

    def write(self, vals):
        def generate(product):
            product.default_code = product._get_default_code_seq_type(
                vals.get('code_seq_type', None))
        for idx, product in enumerate(self):
            if 'default_code' in vals and not vals['default_code']:
                generate(product)
                if idx == len(self) - 1:
                    vals.pop('default_code', None)
        return super().write(vals)
