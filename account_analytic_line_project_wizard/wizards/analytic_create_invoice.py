###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AnalitycCreateInvoice(models.TransientModel):
    _name = 'analytic.create.invoice'
    _description = 'Analytic Create Invoice'

    add_date = fields.Boolean(
        default=True,
        string='Date',
        help='Date of any line will be shown in invoice.',
    )
    add_time = fields.Boolean(
        string='Time',
        help='Time of any line will be shown in invoice.',
    )
    add_description_task = fields.Boolean(
        default=True,
        string='Description task',
        help='Add task descripton to invoice line.',
    )
    add_description = fields.Boolean(
        default=True,
        string='Description',
        help='All description lines will be shown in invoice.',
    )
    product_group = fields.Boolean(
        help='Group invoice lines by product.',
    )
    analytic_price = fields.Boolean(
        help='Analytic price will be used.',
    )
    percent = fields.Float(
        help='Percent to increase analytic cost.',
    )
    force_product = fields.Boolean(
        help='If checked, you must enter a product to invoice.',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
    )

    def _get_selected_lines(self):
        lines = self.env['account.analytic.line'].browse(
            self.env.context.get('active_ids') or [])
        if not lines:
            raise ValidationError(_(
                'Please select at least one analytic line.'))
        return lines

    def _check_billable(self):
        lines = self._get_selected_lines()
        return all(line.task_state == 'to_invoice' for line in lines)

    def _get_task_partner(self):
        lines = self._get_selected_lines()
        partners = lines.mapped('partner_id')
        if not partners or not all(partners):
            raise ValidationError(_(
                'Analytic lines must have defined a partner.'))
        if len(partners.ids) > 1:
            raise ValidationError(_(
                'We can only invoice one partner at a time.'))
        return partners[0]

    def _prepare_task_invoice_values(self):
        partner = self._get_task_partner()
        if not partner:
            raise ValidationError(_(
                'Project and task has not a partner defined and is required.'))
        return {
            'partner_id': partner.id,
            'move_type': 'out_invoice',
            'company_id': self.env.company.id,
        }

    def _get_effective_product(self, line):
        product = self.product_id if self.force_product else line.product_id
        if not product:
            raise ValidationError(_(
                'Each analytic line must have a product or the wizard must be '
                'forced to use one.'))
        return product

    def _get_line_task_name(self, line):
        product = self._get_effective_product(line)
        names = [product.name or '']
        if self.add_description_task:
            names.append(line.task_id.name or '')
        if self.add_description:
            names.append(line.name or '')
        if self.add_date and line.date:
            names.append(line.date.strftime('%d/%m/%Y'))
        if self.add_time:
            names.append(str(line.unit_amount))
            names.append(product.name or '')
        return '-'.join(names)

    def _get_task_account(self, line):
        company = line.company_id or self.env.company
        product = self._get_effective_product(line).with_company(company)
        accounts = product.product_tmpl_id._get_product_accounts()
        if accounts['income']:
            return accounts['income']
        account = self.env['account.account'].search([
            ('company_id', '=', company.id),
            ('account_type', '=', 'income'),
            ('deprecated', '=', False),
        ], limit=1)
        if account:
            return account
        account = self.env['account.account'].search([
            ('company_id', '=', company.id),
            ('account_type', '=', 'income_other'),
            ('deprecated', '=', False),
        ], limit=1)
        if account:
            return account
        raise ValidationError(_(
            'Please configure an income account for the product or company.'))

    def _get_analytic_account(self, line):
        analytic_account = line.task_id.analytic_account_id or \
            line.task_id.project_id.analytic_account_id
        if not analytic_account:
            raise ValidationError(_(
                'The task "%s" does not have an analytic account assigned.')
                % (line.task_id.display_name))
        return analytic_account

    def _get_base_price_unit(self, line):
        product = self._get_effective_product(line)
        if self.analytic_price:
            return abs(
                line.amount / line.unit_amount) if line.unit_amount else 0.0
        if self.percent:
            return abs(
                line.amount / line.unit_amount) if line.unit_amount else 0.0
        return product.lst_price

    def _apply_percent(self, price_unit):
        if self.percent:
            return price_unit * ((self.percent + 100) / 100)
        return price_unit

    def _get_list_data(self):
        sale_order = self.env.context.get('sale_order', False)
        data = []
        lines = self._get_selected_lines()
        if not self.product_group:
            for line in lines:
                if not line.task_id:
                    raise ValidationError(_(
                        'Each analytic line must have a task assigned.'))
                product = self._get_effective_product(line)
                values = {}
                values['product_id'] = product.id
                uom_field = 'product_uom' if sale_order else 'product_uom_id'
                values[uom_field] = product.uom_id.id
                if sale_order:
                    values['product_uom_qty'] = line.unit_amount
                    values['analytic_line_ids'] = [(4, line.id)]
                else:
                    values['quantity'] = line.unit_amount
                    analytic_account = self._get_analytic_account(line)
                    values['analytic_distribution'] = {
                        str(analytic_account.id): 100,
                    }
                values['price_unit'] = self._get_base_price_unit(line)
                values['name'] = self._get_line_task_name(line)
                account = self._get_task_account(line)
                if not sale_order:
                    values['account_id'] = account.id
                    if 'task_id' in self.env['account.move.line']._fields:
                        values['task_id'] = line.task_id.id
                if self.force_product:
                    values['product_id'] = product.id
                values['price_unit'] = self._apply_percent(
                    values['price_unit'])
                data.append(values)
        else:
            products = (
                [self.product_id]
                if self.force_product
                else lines.mapped('product_id'))
            for product in products:
                values = {}
                if self.force_product:
                    product_lines = lines
                else:
                    product_lines = lines.filtered(
                        lambda x: x.product_id == product)
                for line in product_lines:
                    if not line.task_id:
                        raise ValidationError(_(
                            'Each analytic line must have a task assigned.'))
                    effective_product = self._get_effective_product(line)
                    analytic_account = self._get_analytic_account(line)
                    if 'product_id' in values and \
                            effective_product.id == values['product_id']:
                        qty_field = (
                            'product_uom_qty' if sale_order else 'quantity')
                        values[qty_field] += line.unit_amount
                        if self.analytic_price or self.percent:
                            values['price_unit'] += (
                                self._get_base_price_unit(line))
                        else:
                            values['price_unit'] = effective_product.lst_price
                    else:
                        values['product_id'] = effective_product.id
                        uom_field = (
                            'product_uom' if sale_order else 'product_uom_id')
                        qty_field = (
                            'product_uom_qty' if sale_order else 'quantity')
                        values[uom_field] = effective_product.uom_id.id
                        values[qty_field] = line.unit_amount
                        if sale_order:
                            values['analytic_line_ids'] = [(4, line.id)]
                        else:
                            values['analytic_distribution'] = {
                                str(analytic_account.id): 100,
                            }
                        values['price_unit'] = self._get_base_price_unit(line)
                    values['name'] = self._get_line_task_name(line)
                    account = self._get_task_account(line)
                    if not sale_order:
                        values['account_id'] = account.id
                        if 'task_id' in self.env['account.move.line']._fields:
                            values['task_id'] = line.task_id.id
                        if 'analytic_line_ids' not in values:
                            values['analytic_line_ids'] = []
                        values['analytic_line_ids'].append((4, line.id))
                    elif 'analytic_line_ids' in values:
                        values['analytic_line_ids'].append((4, line.id))
                    if self.force_product:
                        values['product_id'] = effective_product.id
                    values['price_unit'] = self._apply_percent(
                        values['price_unit'])
                data.append(values)
        return data

    def _get_lines_data(self):
        if self.env.context.get('sale_order', False):
            self = self.with_context(sale_order=True)
        lines = self._get_list_data()
        data = []
        for line in lines:
            data.append((0, 0, line))
        return data

    def _set_taxes(self, line):
        self.ensure_one()
        company_id = line.company_id or self.env.company
        taxes = line.product_id.taxes_id.filtered(
            lambda r: r.company_id == company_id) or \
            line.account_id.tax_ids or \
            line.move_id.company_id.account_sale_tax_id
        fp_taxes = line.move_id.fiscal_position_id.map_tax(taxes)
        line.tax_ids = fp_taxes
        fix_price = self.env['account.tax']._fix_tax_included_price
        line.price_unit = fix_price(line.price_unit, taxes, fp_taxes)

    def create_invoice(self):
        Move = self.env['account.move'].with_context(
            default_move_type='out_invoice')
        if not self._check_billable():
            raise ValidationError(_(
                'Please, select only billable tasks. You can filter them.'))
        invoice_values = self._prepare_task_invoice_values()
        invoice = Move.create(invoice_values)
        analytic_lines = self._get_selected_lines()
        lines = self._get_lines_data()
        invoice.write({'invoice_line_ids': lines})
        for line in invoice.invoice_line_ids:
            self._set_taxes(line)
        analytic_lines.with_context(skip_task_state_sync=True).write({
            'task_invoice_id': invoice.id,
            'task_state': 'invoiced',
        })
        return invoice

    def create_invoice_and_open(self):
        invoice = self.create_invoice()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = (
                form_view + [(state, view) for state, view in action['views']
                             if view != 'form'])
        else:
            action['views'] = form_view
        action['res_id'] = invoice.id
        return action

    def create_sale_order(self):
        Sale = self.env['sale.order']
        SaleLine = self.env['sale.order.line']
        Tax = self.env['account.tax']
        if not self._check_billable():
            raise ValidationError(_(
                'Please, select only billable tasks. You can filter them.'))
        lines = self._get_selected_lines()
        account = lines.mapped('account_id')
        if len(account) > 1:
            raise ValidationError(_(
                'You must select only 1 analytic account in order to create a '
                'sale order.'))
        sale_values = self._prepare_task_invoice_values()
        del sale_values['move_type']
        sale = Sale.create(sale_values)
        analytic_lines = self._get_selected_lines()
        line_values_list = self.with_context(sale_order=True)._get_list_data()
        created_sale_lines = SaleLine
        for values in line_values_list:
            analytic_commands = values.pop('analytic_line_ids', [])
            values['order_id'] = sale.id
            sale_line = SaleLine.create(values)
            created_sale_lines |= sale_line
            analytic_ids = [
                command[1] for command in analytic_commands
                if isinstance(command, (list, tuple)) and len(command) > 1]
            if analytic_ids:
                self.env['account.analytic.line'].browse(analytic_ids).write({
                    'so_line': sale_line.id,
                })
        sale.write({
            'analytic_account_id': account.id,
        })
        for line in created_sale_lines:
            line._compute_tax_id()
            line.price_unit = Tax._fix_tax_included_price_company(
                line._get_display_price(),
                line.product_id.taxes_id, line.tax_id, line.company_id)
        analytic_lines.write({
            'task_state': 'invoiced',
        })
