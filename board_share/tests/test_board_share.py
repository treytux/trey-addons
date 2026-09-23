###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user


class TestBoardShare(TransactionCase):

    def setUp(self):
        super().setUp()
        self.board_model = self.env['board.board']
        self.board_view = self.env.ref('board.board_my_dash_view')
        self.shared_model = self.env['board.share.dashboard']
        self.owner = new_test_user(
            self.env, 'board_share_owner', 'base.group_user')
        self.recipient = new_test_user(
            self.env, 'board_share_recipient', 'base.group_user')
        self.other_user = new_test_user(
            self.env, 'board_share_other', 'base.group_user')
        self.users_action = self.env.ref('base.action_res_users')
        self.partner_action = self.env.ref('base.action_partner_form')

    def _get_dashboard_arch(self, action_id, label):
        return """
        <form string="My Dashboard">
            <board style="2-1">
                <column>
                    <action name="%s"
                            string="%s"
                            view_mode="list"
                            context="{}"
                            domain="[]"/>
                </column>
            </board>
        </form>
        """ % (action_id, label)

    def _set_dashboard_arch(self, user, action_id, label):
        custom_view = self.env['ir.ui.view.custom'].sudo().search([
            ('user_id', '=', user.id),
            ('ref_id', '=', self.board_view.id),
        ], limit=1)
        arch = self._get_dashboard_arch(action_id, label)
        values = {
            'user_id': user.id,
            'ref_id': self.board_view.id,
            'arch': arch,
        }
        if custom_view:
            custom_view.write({
                'arch': arch,
            })
            return custom_view
        return self.env['ir.ui.view.custom'].sudo().create(values)

    def _create_shared_dashboard(self, name='Sales Snapshot'):
        self._set_dashboard_arch(self.owner, self.users_action.id, 'Users')
        wizard = self.env['board.share.wizard'].with_user(self.owner).create({
            'name': name,
            'user_ids': [(6, 0, [self.recipient.id])],
        })
        wizard.action_share()
        return self.shared_model.with_user(self.owner).search([
            ('name', '=', name),
            ('owner_id', '=', self.owner.id),
        ], limit=1)

    def test_personal_board_arch_is_marked_as_shareable(self):
        self._set_dashboard_arch(self.owner, self.users_action.id, 'Users')
        view = self.board_model.with_user(self.owner).get_view(
            self.board_view.id, 'form')
        self.assertIn('shareable="1"', view['arch'])

    def test_wizard_creates_snapshot_view(self):
        shared = self._create_shared_dashboard()
        self.assertTrue(shared)
        self.assertEqual(shared.owner_id, self.owner)
        self.assertEqual(shared.recipient_ids, self.recipient)
        self.assertTrue(shared.view_id)
        self.assertIn('readonly="1"', shared.view_id.arch_db)
        self.assertNotIn('shareable="1"', shared.view_id.arch_db)
        self.assertIn('string="Sales Snapshot"', shared.view_id.arch_db)

    def test_shared_dashboard_access_is_limited_to_owner_and_recipients(self):
        shared = self._create_shared_dashboard()
        action = shared.with_user(self.recipient).action_open_board()
        self.assertEqual(action['view_id'], shared.view_id.id)
        view = self.board_model.with_user(self.recipient).get_view(
            shared.view_id.id, 'form')
        self.assertIn('readonly="1"', view['arch'])
        with self.assertRaises(AccessError) as error:
            self.board_model.with_user(self.other_user).get_view(
                shared.view_id.id, 'form')
        self.assertEqual(
            str(error.exception),
            'You do not have access to this shared dashboard.'
        )

    def test_snapshot_does_not_change_when_owner_updates_dashboard(self):
        shared = self._create_shared_dashboard()
        self._set_dashboard_arch(self.owner, self.partner_action.id, 'Contacts')
        shared_arch = self.board_model.with_user(self.recipient).get_view(
            shared.view_id.id, 'form')['arch']
        self.assertIn('name="%s"' % self.users_action.id, shared_arch)
        self.assertNotIn('name="%s"' % self.partner_action.id, shared_arch)

    def test_owner_can_rename_and_archive_shared_dashboard(self):
        shared = self._create_shared_dashboard()
        shared.with_user(self.owner).write({
            'name': 'Operations Snapshot',
        })
        self.assertIn('string="Operations Snapshot"', shared.view_id.arch_db)
        self.assertEqual(
            shared.view_id.name,
            'Shared Dashboard: Operations Snapshot')
        shared.with_user(self.owner).write({'active': False})
        with self.assertRaises(UserError) as error_user:
            shared.with_user(self.owner).action_open_board()
        self.assertEqual(
            str(error_user.exception), 'This shared dashboard is archived.')
        with self.assertRaises(AccessError) as error_access:
            self.board_model.with_user(self.recipient).get_view(
                shared.view_id.id, 'form')
        self.assertEqual(
            str(error_access.exception),
            'This shared dashboard is not available.')

    def test_owner_cannot_be_a_recipient(self):
        with self.assertRaises(ValidationError):
            self.shared_model.with_user(self.owner).create({
                'name': 'Invalid Snapshot',
                'recipient_ids': [(6, 0, [self.owner.id])]
            })

    def test_snapshot_sanitizes_group_by_list_context(self):
        self._set_dashboard_arch(self.owner, self.users_action.id, 'Users')
        custom_view = self.env['ir.ui.view.custom'].sudo().search([
            ('user_id', '=', self.owner.id),
            ('ref_id', '=', self.board_view.id),
        ], limit=1)
        custom_view.write({
            'arch': """
                <form string="My Dashboard">
                    <board style="1">
                        <column>
                            <action name="%s"
                                    string="Users"
                                    view_mode="graph"
                                    context="{'group_by': [],
                                    'graph_groupbys': ['login_date:day']}"
                                    domain="[]"/>
                        </column>
                    </board>
                </form>
            """ % self.users_action.id
        })
        shared = self._create_shared_dashboard(name='Grouped Snapshot')
        self.assertTrue(shared.view_id)
        self.assertNotIn("'group_by': []", shared.view_id.arch_db)

    def test_snapshot_removes_group_by_string_context(self):
        self._set_dashboard_arch(self.owner, self.users_action.id, 'Users')
        custom_view = self.env['ir.ui.view.custom'].sudo().search([
            ('user_id', '=', self.owner.id),
            ('ref_id', '=', self.board_view.id),
        ], limit=1)
        custom_view.write({
            'arch': """
                <form string="My Dashboard">
                    <board style="1">
                        <column>
                            <action name="%s"
                                    string="Invoices"
                                    view_mode="pivot"
                                    context="{'group_by': 'invoice_date',
                                    'pivot_row_groupby': ['invoice_date']}"
                                    domain="[]"/>
                        </column>
                    </board>
                </form>
            """ % self.users_action.id
        })
        shared = self._create_shared_dashboard(name='Invoice Snapshot')
        self.assertTrue(shared.view_id)
        self.assertNotIn("'group_by': 'invoice_date'", shared.view_id.arch_db)
