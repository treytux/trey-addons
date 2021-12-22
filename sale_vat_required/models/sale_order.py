###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def check_partner_id_vat(self):
        for sale in self:
            if not sale.partner_id.vat:
                raise ValidationError(_(
                    'The partner %s has not set their VAT') % (
                        sale.partner_id.name))

    @api.multi
    def print_quotation(self):
        self.check_partner_id_vat()
        return super().print_quotation()

    @api.multi
    def action_quotation_send(self):
        self.check_partner_id_vat()
        return super().action_quotation_send()

    @api.multi
    def action_confirm(self):
        if self.state == 'draft':
            self.check_partner_id_vat()
        return super().action_confirm()

    @api.multi
    def preview_sale_order(self):
        self.check_partner_id_vat()
        return super().preview_sale_order()
