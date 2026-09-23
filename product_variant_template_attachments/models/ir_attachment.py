###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None):
        if domain and len(domain) == 2:
            res_id = False
            res_model = False
            for domain_list in domain:
                if domain_list[0] == 'res_id':
                    res_id = domain_list[2]
                elif domain_list[0] == 'res_model':
                    res_model = domain_list[2]
            if res_id and res_model and res_model == 'product.product':
                product = self.env['product.product'].browse(res_id)
                if product:
                    domain.insert(0, '|')
                    domain.insert(1, '&')
                    domain += [
                        '&',
                        ('res_id', '=', product.product_tmpl_id.id),
                        ('res_model', '=', 'product.template'),
                    ]
        return super().search_read(
            fields=fields, offset=offset, limit=limit, domain=domain,
            order=order)
