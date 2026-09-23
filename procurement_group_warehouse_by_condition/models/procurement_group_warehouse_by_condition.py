###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProcurementGroupWarehouseByCondition(models.Model):
    _name = 'procurement.group.warehouse_by_condition'
    _description = 'Procurement group warehouse by condition.'

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse by condition',
        required=True,
        domain="[('is_warehouse_by_condition', '=', True)]",
    )
    line_ids = fields.One2many(
        comodel_name='procurement.group.warehouse_by_condition.line',
        inverse_name='warehouse_by_condition_id',
        string='Lines',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )

    @api.constrains('warehouse_id')
    def _check_warehouse_id_unique(self):
        conditions = self.search([
            ('id', '!=', self.id),
            ('warehouse_id', '=', self.warehouse_id.id),
        ])
        if conditions:
            raise ValidationError(_(
                'Another condition procurement group warehouse already exists '
                'for warehouse %s.') % self.warehouse_id.name)

    @api.constrains('line_ids')
    def _check_exist_line_ids(self):
        if not self.line_ids:
            raise ValidationError(_(
                'You must add at least one condition line.'))

    @api.constrains('line_ids')
    def _check_duplicate_line_ids(self):
        line_obj = self.env['procurement.group.warehouse_by_condition.line']
        for line in self.line_ids:
            domain = [
                ('id', '!=', line.id),
                ('sign', '=', line.sign),
                ('quantity', '=', line.quantity),
                ('zips', '=', line.zips),
                ('main_warehouse_id', '=', line.main_warehouse_id.id),
            ]
            if line.applied_on == 'product_category':
                line_categ_id = line.product_category_id.id
                domain.append(('product_category_id', '=', line_categ_id))
            elif line.applied_on == 'product_template':
                line_product_tmpl_id = line.product_tmpl_id.id
                domain.append(('product_tmpl_id', '=', line_product_tmpl_id))
            elif line.applied_on == 'product_variant':
                domain.append(('product_id', '=', line.product_id.id))
            line_conditions = line_obj.search(domain)
            if line_conditions:
                raise ValidationError(_(
                    'Condition line repeated for warehouse %s. You can not '
                    'more than one line with the same conditions.'
                ) % self.warehouse_id.name)

    def get_user_id(self, sale):
        return (
            self.env.user.company_id.notification_user_id.id
            or sale.user_id.id or self.env.user.id
        )

    def notificate_error(self, sale, msg):
        sale.activity_schedule(
            summary=_(
                'Procurement group warehouse by condition fail; check errors.'
            ),
            act_type_xmlid='mail.mail_activity_data_warning',
            user_id=self.get_user_id(sale),
            note=msg,
            date_deadline=fields.Date.today(),
        )
        body = _('Error: <b>%s</b>') % msg
        sale.message_post(body=body)

    def search_condition_lines(self, lines, product):
        condition_lines = self.env[
            'procurement.group.warehouse_by_condition.line']
        for line in lines:
            if line.applied_on == 'product_variant':
                condition_lines |= self.line_ids.filtered(
                    lambda ln: ln.product_id == product)
            elif line.applied_on == 'product_template':
                condition_lines |= self.line_ids.filtered(
                    lambda ln: product
                    in ln.product_tmpl_id.product_variant_ids)
            elif line.applied_on == 'product_category':
                products = self.env['product.product'].search([
                    ('categ_id', '=', line.product_category_id.id),
                ])
                condition_lines |= self.line_ids.filtered(
                    lambda ln: product in products)
            elif line.applied_on == 'product_global':
                all_products = self.env['product.product'].search([])
                condition_lines |= self.line_ids.filtered(
                    lambda ln: product in all_products)
        return condition_lines

    def get_condition_line(self, product, quantity, zip_code, sale):
        self.ensure_one()
        condition_eval_log = ''
        condition_line_found = False
        main_warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        condition_lines = self.search_condition_lines(self.line_ids, product)
        if not zip_code and all(condition_lines.mapped('zips')):
            msg = _(
                'The partner shipping address does not have a zip code. '
                'The company\'s default warehouse is assigned: \'%s\'.') % (
                    main_warehouse.name)
            self.notificate_error(sale, msg)
            return False
        for condition_line in condition_lines:
            condition_to_eval = '%s %s %s' % (
                quantity, condition_line.sign, condition_line.quantity)
            condition_zip = '%s in [%s]' % (zip_code, condition_line.zips)
            if condition_line.zips:
                condition_to_eval += ' and %s' % condition_zip
            condition_eval_log += '\n%s' % condition_to_eval
            if eval(condition_to_eval):
                condition_line_found = condition_line
                condition_evaluated = condition_to_eval
                break
        if not condition_lines:
            msg = _(
                'No condition line found for warehouse \'%s\' for the product '
                '\'%s\'. The company\'s default warehouse is assigned: \'%s\'.'
            ) % (
                self.warehouse_id.name, product.display_name,
                main_warehouse.name)
            self.notificate_error(sale, msg)
            return False
        if not condition_line_found:
            msg = _(
                'No condition line found for warehouse \'%s\' for the product '
                '\'%s\' that matches the conditions: %s. The company\'s '
                'default warehouse is assigned: \'%s\'.') % (
                    self.warehouse_id.name, product.display_name,
                    condition_eval_log, main_warehouse.name)
            self.notificate_error(sale, msg)
            return False
        if condition_line_found.applied_on == 'product_global':
            applied_on_msg = 'All products'
        elif condition_line_found.applied_on == 'product_category':
            applied_on_msg = (
                'Product category: %s' % (
                    condition_line_found.product_category_id.name))
        elif condition_line_found.applied_on == 'product_template':
            applied_on_msg = (
                'Product template: %s' % (
                    condition_line_found.product_tmpl_id.display_name))
        else:
            applied_on_msg = (
                'Product variant: %s' % (
                    condition_line_found.product_id.display_name))
        msg = _(
            '<ul>'
            '    <li>Warehouse selected in the order: \'%s\'</li>'
            '    <li>Order line data:'
            '        <ul>'
            '            <li>%s</li>'
            '            <li>Quantity: %s</li>'
            '            <li>Partner address zip: %s</li>'
            '        </ul>'
            '    </li>'
            '    <li>Condition applied: %s'
            '        <ul>'
            '            <li>Warehouse by conditions: %s</li>'
            '            <li>Sequence: %s</li>'
            '            <li>%s</li>'
            '            <li>Sign: %s</li>'
            '            <li>Quantity: %s</li>'
            '            <li>Zips: %s</li>'
            '            <li>Main warehouse: %s</li>'
            '            <li>Alternative warehouses: %s</li>'
            '        </ul>'
            '    </li>'
            '</ul>'
        ) % (
            sale.warehouse_id.name,
            applied_on_msg,
            quantity,
            zip_code or '',
            condition_evaluated,
            condition_line_found.warehouse_by_condition_id.warehouse_id.name,
            condition_line_found.sequence,
            applied_on_msg,
            condition_line_found.sign.replace(
                '&lt;', '<').replace('&gt;', '>'),
            condition_line_found.quantity,
            condition_line_found.zips or '',
            condition_line_found.main_warehouse_id.name,
            ', '.join(
                condition_line_found.alternative_warehouse_ids.mapped('name')))
        body = _(
            'Procurement group warehouse by conditions: <b>%s</b>.') % msg
        sale.message_post(body=body)
        return condition_line_found
