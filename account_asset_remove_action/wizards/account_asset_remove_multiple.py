###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class AccountAssetRemoveMultiple(models.TransientModel):
    _name = 'account.asset.remove.multiple'
    _inherit = 'account.asset.remove'
    _description = 'Wizard to remove multiple assets from tree view'

    @api.multi
    def button_accept(self):
        self.ensure_one()
        wizard_obj = self.env['account.asset.remove']
        active_ids = self.env.context.get('active_ids', [])
        assets = self.env['account.asset'].browse(active_ids)
        account_move_ids = []
        for asset in assets:
            ctx = dict(
                self.env.context, active_ids=asset.ids, active_id=asset.id)
            early_removal = False
            if asset.method in ['linear-limit', 'degr-limit']:
                if asset.value_residual != asset.salvage_value:
                    early_removal = True
            elif asset.value_residual:
                early_removal = True
            if early_removal:
                ctx.update({'early_removal': True})
            wizard = wizard_obj.with_context(ctx).create({
                'date_remove': self.date_remove,
                'force_date': self.force_date,
                'sale_value': self.sale_value,
                'account_sale_id': self.account_sale_id.id,
                'account_plus_value_id': self.account_plus_value_id.id,
                'account_min_value_id': self.account_min_value_id.id,
                'account_residual_value_id': self.account_residual_value_id.id,
                'posting_regime': self.posting_regime,
            })
            res = wizard.remove()
            account_move_ids.append(res['domain'][0][2])
        form_view = self.env.ref('account.view_move_form')
        tree_view = self.env.ref('account.view_move_tree')
        search_view = self.env.ref('account.view_account_move_filter')
        action_vals = {
            'name': _('Asset removal journal entry'),
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', account_move_ids)],
        }
        if len(account_move_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': account_move_ids[0],
            })
        return action_vals
