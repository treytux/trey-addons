###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models


class SaleOrderLinesByRef(models.TransientModel):
    _name = 'sale.order.lines_by_ref'
    _description = 'Create sale order line by refs'

    def _get_default_sale_order(self):
        return self.env['sale.order'].browse(self._context.get('active_id'))

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        default=_get_default_sale_order,
        required=True,
        ondelete='cascade',
    )
    references = fields.Text(
        string='References',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='sale.order.lines_by_ref.message',
        inverse_name='wizard_id',
        string='Messages',
    )
    step = fields.Integer(
        string='step',
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def _error(self, message, ref):
        self.ensure_one()
        self.line_ids.create({
            'wizard_id': self.id,
            'name': message,
            'ref': ref,
        })

    def _warning(self, message, ref):
        self.ensure_one()
        self.line_ids.create({
            'type': 'warning',
            'wizard_id': self.id,
            'name': message,
            'ref': ref,
        })

    def references_to_list(self):
        self.ensure_one()
        txt = self.references
        txt = txt.split('\n')
        txt = [t.strip() for t in txt]
        return [t for t in txt if t]

    def _reference_error(self, default_code):
        self._error(_('Ref not exists'), default_code)

    def _get_product_by_ref(self, default_code):
        products = self.env['product.product'].search([
            ('sale_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        if not products:
            products = self._reference_error(default_code)
        return products

    def get_customerinfo_domain(self, default_code):
        domain = [('product_code', '=', default_code)]
        if self.sale_id.partner_id == self.sale_id.partner_shipping_id:
            domain.append(('name', '=', self.sale_id.partner_id.id))
        else:
            domain.append(('|'))
            domain.append(('name', '=', self.sale_id.partner_id.id))
            domain.append(('name', '=', self.sale_id.partner_shipping_id.id))
        return domain

    def search_product_customerinfo(self, customerinfos):
        products = self.env['product.product']
        for customerinfo in customerinfos:
            if customerinfo.product_id:
                return customerinfo.product_id
            elif customerinfo.product_tmpl_id.product_variant_id:
                return customerinfo.product_tmpl_id.product_variant_id
        return products

    def _get_product_by_customer_code(self, default_code):
        products = self.env['product.product']
        product = products
        products_customer = self.env['product.customerinfo'].search(
            self.get_customerinfo_domain(default_code))
        if products_customer:
            product = products_customer[0]
            products_tmpl = product.product_tmpl_id.product_variant_ids
        if len(products_customer) == 1:
            if products_customer.product_id:
                products = product.product_id
            else:
                if len(products_tmpl) > 1:
                    products = self.env['product.product']
                    self._error(
                        _('More than 1 variant for the same default_code'),
                        default_code)
                elif len(products_customer[0].product_tmpl_id) == 1:
                    products = products_tmpl
                else:
                    products = self.env['product.product']
                    self._reference_error(default_code)
        elif len(products_customer) > 1:
            if self.sale_id.partner_id == self.sale_id.partner_shipping_id:
                products = self.search_product_customerinfo(products_customer)
            else:
                products = self.search_product_customerinfo(
                    products_customer.filtered(
                        lambda c: c.name == self.sale_id.partner_shipping_id))
                if not products:
                    products = self.search_product_customerinfo(
                        products_customer.filtered(
                            lambda c: c.name == self.sale_id.partner_id))
        else:
            products = self._get_product_by_ref(default_code)
        return products

    def _prepare_sale_line(self, ref):
        def _float(value, default=None):
            try:
                return float(value)
            except Exception:
                return default

        get_param = self.env['ir.config_parameter'].sudo().get_param
        vals = ref.split(get_param('sale_order_lines_by_ref.glue', '/'))
        default_code = vals.pop(0)
        modules = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'product_supplierinfo_for_customer_sale'),
            ('state', '=', 'installed'),
        ])
        if not modules:
            products = self._get_product_by_ref(default_code)
        else:
            products = self._get_product_by_customer_code(default_code)
        data = {
            'order_id': self.sale_id.id,
            'product_id': products[0].id if products else False,
            'product_uom_qty': 1,
        }
        if vals:
            data['product_uom_qty'] = _float(vals.pop(0), 1)
        if vals:
            price_unit = _float(vals.pop(0))
            if price_unit:
                data['price_unit'] = price_unit
        return default_code, data

    def action_simulate(self):
        self.ensure_one()
        self.line_ids.unlink()
        for ref in self.references_to_list():
            default_code, data_line = self._prepare_sale_line(ref)
            if not data_line['order_id']:
                self._error(
                    _('Must be launch this wizard from sale order'),
                    default_code)
                continue
        self.step = 1
        return self._reopen_view()

    def action_back(self):
        self.step = 0
        return self._reopen_view()

    def _create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = self._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = record
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def post_create_lines(self, lines):
        pass

    def action_create(self):
        line_obj = self.env['sale.order.line']
        lines = self.env['sale.order.line']
        for ref in self.references_to_list():
            default_code, data_line = self._prepare_sale_line(ref)
            if default_code in self.line_ids.mapped('ref'):
                continue
            if not data_line['product_id']:
                continue
            lines |= self._create_with_onchange(line_obj, data_line)
        self.post_create_lines(lines)

    def action_simulate_and_create(self):
        res = self.action_simulate()
        if not self.line_ids:
            self.action_create()
            return
        return res


class SaleOrderLinesByRefMessage(models.TransientModel):
    _name = 'sale.order.lines_by_ref.message'
    _description = 'Message for create sale order line by refs'
    _order = 'ref'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.lines_by_ref',
        string='Wizard',
    )
    type = fields.Selection(
        selection=[
            ('error', 'Error'),
            ('warning', 'Warning'),
        ],
        string='Type',
        default='error',
    )
    name = fields.Char(
        string='Message',
        required=True,
    )
    ref = fields.Char(
        string='Reference',
        required=True,
    )
