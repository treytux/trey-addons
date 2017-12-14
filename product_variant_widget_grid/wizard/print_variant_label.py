# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, exceptions, _


class PrintVariantLabel(models.TransientModel):
    _name = 'print.variant.label'

    @api.model
    def _get_domain_report(self):
        reports = self.env['ir.actions.report.xml'].with_context(
            lang='en_US').search([('name', 'ilike', '(product_label)')])
        return [('id', 'in', reports and reports.ids or [0])]

    def _get_default_report(self):
        reports = self.env['ir.actions.report.xml'].with_context(
            lang='en_US').search([('name', 'ilike', '(product_label)')])
        return reports and reports[0].id or None

    @api.model
    def _get_domain_product(self):
        product_tmpl_ids = [
            p.id for p in self.env['product.template'].search([])
            if len(p.attribute_line_ids) <= 2]
        return [('attribute_line_ids', '!=', False),
                ('id', 'in', product_tmpl_ids or [0])]

    def _get_default_product(self):
        return self.env.context['active_id'] or None

    report_id = fields.Many2one(
        comodel_name='ir.actions.report.xml',
        string='Report',
        domain=_get_domain_report,
        default=_get_default_report,
        required=True)
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        domain=_get_domain_product,
        default=_get_default_product,
        required=True)
    variant_line_ids = fields.Many2many(
        comodel_name='print.variant.label.line',
        relation='product_variant_label_line_rel',
        column1='product_variant',
        column2='product_variant_line')

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        fields = ('product_id', 'disabled', 'quantity',
                  'value_x', 'value_y', 'label_x', 'label_y')
        [[field_onchange.setdefault('variant_line_ids.%s' % sub, u'')
         for sub in fields] if 'variant_line_ids' in field_onchange else None]
        return super(PrintVariantLabel, self).onchange(
            values, field_name, field_onchange)

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        def _create_line(attr_lines, product_variants, value_x, value_y):
            if len(attr_lines) == 1:
                product = product_variants.filtered(
                    lambda x: (value_x in x.attribute_value_ids))
                value_y = (product.attribute_value_ids[0].attribute_id)
            else:
                product = product_variants.filtered(
                    lambda x: (value_x in x.attribute_value_ids and
                               value_y in x.attribute_value_ids))
            return (0, 0, {
                'product_id': product, 'disabled': not bool(product),
                'value_x': value_x.id, 'value_y': value_y.id, 'quantity': 0})

        attr_lines = self.product_tmpl_id.attribute_line_ids
        if not 1 <= len(attr_lines) <= 2:
            msg = _('Wizard grid only be able shows products that has '
                    'one or two attributes')
            raise exceptions.Warning(msg)
        prod_variants = self.product_tmpl_id.product_variant_ids
        y_dict_value = (attr_lines[1].value_ids if len(attr_lines) == 2
                        else self.product_tmpl_id)
        lines = []
        self.variant_line_ids = [(6, 0, [])]
        for value_x in attr_lines[0].value_ids:
            for value_y in y_dict_value:
                lines.append(
                    _create_line(
                        attr_lines, prod_variants, value_x, value_y))
            self.variant_line_ids = lines

    @api.multi
    def button_print_labels(self):
        variant_ids = []
        for line in self.variant_line_ids:
            if line.quantity:
                variant_ids.extend([line.product_id.id] * line.quantity)
        if not variant_ids:
            raise exceptions.ValidationError(
                _('Please, enter at least one quantity'))
        return {'type': 'ir.actions.report.xml',
                'report_name': self.report_id.report_name,
                'datas': {'ids': variant_ids},
                'context': {'report_name': self.report_id.report_name,
                            'show_origin': False}}


class PrintVariantLabelLine(models.TransientModel):
    _name = 'print.variant.label.line'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Variant',
        readonly=True)
    disabled = fields.Boolean(
        string='Disabled')
    value_x = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Value x')
    label_x = fields.Char(
        string='X',
        related='value_x.name')
    value_y = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Value y')
    label_y = fields.Char(
        string='Y',
        compute='_compute_label')
    quantity = fields.Integer(
        string='Quantity')

    @api.one
    @api.depends('product_id')
    def _compute_label(self):
        attrs = self.product_id.product_tmpl_id.attribute_line_ids
        self.label_y = (len(attrs) == 1 and attrs[0].attribute_id.name or
                        self.value_y.name)
