###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    def _map_account_by_medium(self, account, medium_id=False):
        if not medium_id:
            medium_id = self.env.context.get('medium_id')
        if not medium_id and 'active_model' in self.env.context:
            record = self.env[self.env.context['active_model']].browse(
                self.env.context.get('active_id')
            )
            if record._fields.get('medium_id'):
                medium_id = record.medium_id.id
        if not medium_id:
            return account
        for ln in self.account_ids:
            if ln.account_src_id == account and ln.medium_id.id == medium_id:
                return ln.account_dest_id
        return account

    def map_account(self, account):
        account = self._map_account_by_medium(account)
        if account:
            return account
        position = self.new(origin=self)
        position.account_ids = self.account_ids.filtered(
            lambda ln: not ln.medium_id)
        return super(AccountFiscalPosition, position).map_account(account)

    def map_accounts(self, accounts):
        position = self.new(origin=self)
        position.account_ids = self.account_ids.filtered(
            lambda ln: not ln.medium_id)
        accounts = super(AccountFiscalPosition, position).map_accounts(
            accounts)
        for key, acc in accounts.items():
            accounts[key] = self._map_account_by_medium(acc)
        return accounts
