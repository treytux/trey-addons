###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################


class ContractLiteTestCommonMixin:
    def _ensure_sale_journal(self, company):
        journal = self.env['account.journal'].search(
            [
                ('type', '=', 'sale'),
                ('company_id', '=', company.id),
            ],
            limit=1,
        )
        if not journal:
            journal = self.env['account.journal'].create(
                {
                    'name': 'Test Sales Journal',
                    'code': 'TSJ',
                    'type': 'sale',
                    'company_id': company.id,
                }
            )
        return journal

    def _ensure_partner_accounts(self, partner, company):
        account_obj = self.env['account.account']
        receivable_account = account_obj.search(
            [
                ('account_type', '=', 'asset_receivable'),
                ('company_id', 'in', [company.id, False]),
                ('deprecated', '=', False),
            ],
            limit=1,
        )
        if not receivable_account:
            receivable_account = account_obj.create(
                {
                    'code': 'TCL430',
                    'name': 'Contract Lite Receivable',
                    'account_type': 'asset_receivable',
                    'company_id': company.id,
                    'reconcile': True,
                }
            )
        payable_account = account_obj.search(
            [
                ('account_type', '=', 'liability_payable'),
                ('company_id', 'in', [company.id, False]),
                ('deprecated', '=', False),
            ],
            limit=1,
        )
        if not payable_account:
            payable_account = account_obj.create(
                {
                    'code': 'TCL400',
                    'name': 'Contract Lite Payable',
                    'account_type': 'liability_payable',
                    'company_id': company.id,
                    'reconcile': True,
                }
            )
        partner.property_account_receivable_id = receivable_account
        partner.property_account_payable_id = payable_account

    def _get_test_product(self):
        product = self.env['product.product'].search(
            [('detailed_type', '=', 'service')],
            limit=1,
        )
        if not product:
            product = self.env['product.product'].search([], limit=1)
        if not product:
            self.skipTest('No product available to build contract_lite fixtures')
        return product

    def _ensure_income_account_for_product(self, product, company):
        income_account = self.env['account.account'].search(
            [
                ('account_type', '=', 'income'),
                ('company_id', 'in', [company.id, False]),
                ('deprecated', '=', False),
            ],
            limit=1,
        )
        if not income_account:
            income_account = self.env['account.account'].create(
                {
                    'code': 'TCL700',
                    'name': 'Contract Lite Income',
                    'account_type': 'income',
                    'company_id': company.id,
                }
            )
        product_tmpl = product.product_tmpl_id.with_company(company)
        if 'property_account_income_id' in product_tmpl._fields:
            product_tmpl.property_account_income_id = income_account
        categ = product_tmpl.categ_id.with_company(company)
        if 'property_account_income_categ_id' in categ._fields:
            categ.property_account_income_categ_id = income_account

    def _create_contract_line(
        self,
        contract,
        product,
        date_start,
        recurring_next_date,
        **overrides
    ):
        vals = {
            'contract_id': contract.id,
            'product_id': product.id,
            'automatic_price': True,
            'quantity': 1.0,
            'uom_id': product.uom_id.id,
            'discount': 0.0,
            'name': 'Service #START_MONTH_INT#/#START_YEAR#',
            'recurring_interval': 1,
            'recurring_rule_type': 'monthly',
            'date_start': date_start,
            'recurring_next_date': recurring_next_date,
        }
        vals.update(overrides)
        return self.env['contract_lite.line'].create(vals)
