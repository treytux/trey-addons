###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models
from openerp.tools import float_compare


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_termoclub = fields.Boolean(
        related='product_tmpl_id.is_termoclub',
    )

    @api.multi
    def termoclub_check_stock(self):
        self.ensure_one()
        supplier = self.env.user.company_id.termoclub_supplier_id
        termoclub = self.env.user.company_id.termoclub_client()
        client = termoclub.connection()
        if not self.is_termoclub:
            return _('Not TermoClub product: %s\n' % self.name)
        supplier_info = self.product_tmpl_id.seller_ids.filtered(
            lambda l: l.name == supplier)
        if not supplier_info.product_code:
            return _('No product supplier code for %s\n' % self.name)
        res = termoclub.get_product(client=client,
                                    product=supplier_info.product_code)
        if res.find('error'):
            return _('TermoClub error: %s\n' % res.find('error').text)
        if res.find('art1') is None:
            return _('TermoClub error: Product no found')
        product = res.find('art1')
        msg = _('TermoClub code: %s\n' % product.find('codart').text)
        msg += _('TermoClub description: %s\n' % product.find('descrip').text)
        msg += _('TermoClub stock: %s\n' % product.find('stoalm').text)
        msg += _('TermoClub minimum unit: %s\n' % product.find('venmin').text)
        if (not self.env.user.has_group('base.user_admin') or not
                self.env.user.has_group('purchase.group_purchase_manager')):
            return msg
        msg += _('TermoClub price: %s\n' % product.find('preven').text)
        msg += _('TermoClub discount: %s\n' % product.find('dto').text)
        new_price = float(product.find('preven').text)
        if not bool(float_compare(supplier_info.price, new_price, 2) != 0):
            return msg
        self.product_tmpl_id.message_post(
            body=_('The supplier price is changed, old: %s new: %s <p>' % (
                supplier_info.price, new_price)))
        supplier_info.write({
            'price': new_price,
        })
        self.env.cr.commit()
        return msg

    @api.multi
    def action_termoclub_check_stock(self):
        self.ensure_one()
        if not self.is_termoclub:
            return
        message = self.termoclub_check_stock()
        raise exceptions.UserError(message)
