###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class ResPartnerGoodsFree(models.Model):
    _name = 'res.partner.goods_free'
    _description = 'Partner promotions goods free agreement'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    percent = fields.Float(
        string='Goods free (%)',
    )

    @api.constrains('product_id', 'partner_id')
    def _check_duplicated_agreements(self):
        for agreement in self:
            records = agreement.search([
                ('id', '!=', agreement.id),
                ('partner_id', '=', agreement.partner_id.id),
                ('product_id', '=', agreement.product_id.id),
            ])
            if not records:
                continue
            raise exceptions.ValidationError(_(
                'There can only be a free goods agreement for the same '
                'product "%s" and partner "%s".') % (
                    agreement.product_id.name, agreement.partner_id.name))
