###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class PurchaseOrderLinesByRef(models.TransientModel):
    _name = 'purchase.order.lines_by_ref'
    _description = 'Wizard to create purchase order lines by refs'

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='cascade',
    )
    references = fields.Text(
        string='References',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='purchase.order.lines_by_ref.message',
        inverse_name='wizard_id',
        string='Messages',
    )
    step = fields.Integer(
        string='Step',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['purchase_id'] = self.env.context.get(
            'order_id', self.env.context.get(
                'active_id', False))
        return res

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
            ('purchase_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        if not products:
            products = self._reference_error(default_code)
        return products

    def get_supplierinfo_domain(self, default_code):
        return [
            ('partner_id', '=', self.purchase_id.partner_id.id),
            ('product_code', '=', default_code),
        ]

    def get_supplierinfo_product(self, products):
        supplierinfo_obj = self.env['product.supplierinfo']
        supplierinfo = supplierinfo_obj.search([
            ('partner_id', '=', self.purchase_id.partner_id.id),
            ('product_id', '=', products[0].id),
        ])
        if not supplierinfo:
            supplierinfo = supplierinfo_obj.search([
                ('partner_id', '=', self.purchase_id.partner_id.id),
                ('product_tmpl_id', '=', products[0].product_tmpl_id.id),
            ])
        return supplierinfo

    def search_product_supplierinfo(self, supplierinfos):
        products = self.env['product.product']
        for supplierinfo in supplierinfos:
            if supplierinfo.product_id:
                return supplierinfo.product_id
            elif supplierinfo.product_tmpl_id.product_variant_id:
                return supplierinfo.product_tmpl_id.product_variant_id
        return products

    def _get_product_by_supplier_code(self, default_code):
        products = self.env['product.product']
        product = products
        products_supplier = self.env['product.supplierinfo'].search(
            self.get_supplierinfo_domain(default_code))
        if products_supplier:
            product = products_supplier[0]
            products_variants = product.product_tmpl_id.product_variant_ids
        if len(products_supplier) == 1:
            if products_supplier.product_id:
                products = product.product_id
            else:
                if len(products_variants) > 1:
                    products = self.env['product.product']
                    self._error(
                        _('More than 1 variant for the same default_code'),
                        default_code)
                elif len(products_supplier[0].product_tmpl_id) == 1:
                    products = products_variants
                else:
                    products = self.env['product.product']
                    self._reference_error(default_code)
        elif len(products_supplier) > 1:
            products = self.search_product_supplierinfo(products_supplier)
        else:
            products = self._get_product_by_ref(default_code)
        return products

    def _prepare_purchase_line(self, ref):
        def _float(value, default=None):
            try:
                return float(value)
            except Exception:
                return default

        get_param = self.env['ir.config_parameter'].sudo().get_param
        vals = ref.split(get_param('purchase_order_lines_by_ref.glue', '/'))
        default_code = vals.pop(0)
        products = self._get_product_by_supplier_code(default_code)
        data = {
            'order_id': self.purchase_id.id,
            'product_id': products[0].id if products else False,
            'product_qty': 1,
        }
        if vals:
            data['product_qty'] = _float(vals.pop(0), 1)
        if vals:
            price_unit = _float(vals.pop(0))
            if price_unit:
                data['price_unit'] = price_unit
        elif products:
            products_supplier = self.get_supplierinfo_product(products)
            if products_supplier:
                data['price_unit'] = products_supplier[0].price
        return default_code, data

    def action_simulate(self):
        self.ensure_one()
        self.line_ids.unlink()
        for ref in self.references_to_list():
            default_code, data_line = self._prepare_purchase_line(ref)
            if not data_line['order_id']:
                self._error(
                    _('Must be launch this wizard from purchase order'),
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
        data = record._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        res = {
            'value': {},
            'warnings': set(),
        }
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
                new.update(data)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def post_create_lines(self, lines):
        pass

    def action_create(self):
        line_obj = self.env['purchase.order.line']
        lines = self.env['purchase.order.line']
        for ref in self.references_to_list():
            default_code, data_line = self._prepare_purchase_line(ref)
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


class PurchaseOrderLinesByRefMessage(models.TransientModel):
    _name = 'purchase.order.lines_by_ref.message'
    _description = 'Message for create purchase order line by refs'
    _order = 'ref'

    wizard_id = fields.Many2one(
        comodel_name='purchase.order.lines_by_ref',
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
