###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


class ContractLiteSupplierTestCommonMixin:
    def _ensure_purchase_journal(self, company):
        journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', company.id),
        ], limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Test Purchase Journal',
                'code': 'TPJ',
                'type': 'purchase',
                'company_id': company.id,
            })
        return journal

    def _ensure_partner_accounts(self, partner, company):
        account_obj = self.env['account.account']
        receivable_account = account_obj.search([
            ('account_type', '=', 'asset_receivable'),
            ('company_id', 'in', [company.id, False]),
            ('deprecated', '=', False),
        ], limit=1)
        payable_account = account_obj.search([
            ('account_type', '=', 'liability_payable'),
            ('company_id', 'in', [company.id, False]),
            ('deprecated', '=', False),
        ], limit=1)
        if receivable_account:
            partner.property_account_receivable_id = receivable_account
        if payable_account:
            partner.property_account_payable_id = payable_account

    def _get_test_product(self):
        product = self.env['product.product'].search([
            ('detailed_type', '=', 'service'),
        ], limit=1)
        if not product:
            product = self.env['product.product'].search([], limit=1)
        if not product:
            self.skipTest('No product available to build supplier contracts')
        return product

    def _ensure_expense_account_for_product(self, product, company):
        expense_account = self.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('company_id', 'in', [company.id, False]),
            ('deprecated', '=', False),
        ], limit=1)
        if not expense_account:
            expense_account = self.env['account.account'].create({
                'code': 'CLS600',
                'name': 'Contract Lite Supplier Expense',
                'account_type': 'expense',
                'company_id': company.id,
            })
        product_tmpl = product.product_tmpl_id.with_company(company)
        if 'property_account_expense_id' in product_tmpl._fields:
            product_tmpl.property_account_expense_id = expense_account
        categ = product_tmpl.categ_id.with_company(company)
        if 'property_account_expense_categ_id' in categ._fields:
            categ.property_account_expense_categ_id = expense_account

    def _create_contract_line(self, contract, product, date_start,
                              recurring_next_date, **overrides):
        vals = {
            'contract_id': contract.id,
            'product_id': product.id,
            'automatic_price': True,
            'quantity': 1.0,
            'uom_id': product.uom_id.id,
            'discount': 0.0,
            'name': 'Supplier service #START_MONTH_INT#/#START_YEAR#',
            'recurring_interval': 1,
            'recurring_rule_type': 'monthly',
            'date_start': date_start,
            'recurring_next_date': recurring_next_date,
        }
        vals.update(overrides)
        return self.env['contract_lite_supplier.line'].create(vals)
