###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from pathlib import Path

from odoo.tests.common import TransactionCase, tagged


@tagged('sale_order_calendar_lock', 'post_install', '-at_install')
class TestSaleOrderCalendarLock(TransactionCase):

    def setUp(self):
        super().setUp()
        module_root = Path(__file__).resolve().parents[1]
        self.js_source = (
            module_root / 'static' / 'src' / 'js' / 'sale_order_calendar_no_move.js'
        ).read_text(encoding='utf-8')

    def test_draft_state_event_is_editable(self):
        self.assertIn('const isLocked = state !== "draft";', self.js_source)

    def test_non_draft_state_event_locked(self):
        self.assertIn('event.editable = false;', self.js_source)
