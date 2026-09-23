###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestUtmMediumSmartbuttons(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.utm_medium = self.env['utm.medium'].create({
            'name': 'Test Medium',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 50.0,
        })

    def _create_sale_order(self, medium):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'medium_id': medium.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

    def _create_invoice(self, medium):
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'medium_id': medium.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        return invoice

    def _create_lead(self, medium):
        return self.env['crm.lead'].create({
            'name': 'Test Lead',
            'partner_id': self.partner.id,
            'medium_id': medium.id,
            'type': 'lead',
        })

    def test_quotation_count_compute(self):
        self.assertEqual(self.utm_medium.quotation_count, 0)
        self._create_sale_order(self.utm_medium)
        self.utm_medium._compute_quotation_count()
        self.assertEqual(self.utm_medium.quotation_count, 1)
        sale_2 = self._create_sale_order(self.utm_medium)
        self.utm_medium._compute_quotation_count()
        self.assertEqual(self.utm_medium.quotation_count, 2)
        sale_2.action_cancel()
        self.utm_medium._compute_quotation_count()
        self.assertEqual(self.utm_medium.quotation_count, 2)

    def test_invoiced_amount_compute(self):
        self.assertEqual(self.utm_medium.invoiced_amount, 0)
        invoice_1 = self._create_invoice(self.utm_medium)
        invoice_1.action_post()
        self.utm_medium._compute_sale_invoiced_amount()
        self.assertEqual(self.utm_medium.invoiced_amount, 100.0)
        invoice_2 = self._create_invoice(self.utm_medium)
        invoice_2.action_post()
        self.utm_medium._compute_sale_invoiced_amount()
        self.assertEqual(self.utm_medium.invoiced_amount, 200.0)

    def test_invoiced_amount_compute_draft_invoice(self):
        self.assertEqual(self.utm_medium.invoiced_amount, 0)
        invoice = self._create_invoice(self.utm_medium)
        self.utm_medium._compute_sale_invoiced_amount()
        self.assertEqual(self.utm_medium.invoiced_amount, 0)
        invoice.action_post()
        self.utm_medium._compute_sale_invoiced_amount()
        self.assertEqual(self.utm_medium.invoiced_amount, 100.0)

    def test_crm_lead_count_compute(self):
        self.assertEqual(self.utm_medium.crm_lead_count, 0)
        self._create_lead(self.utm_medium)
        self.utm_medium._compute_crm_lead_count()
        self.assertEqual(self.utm_medium.crm_lead_count, 1)
        lead_2 = self._create_lead(self.utm_medium)
        self.utm_medium._compute_crm_lead_count()
        self.assertEqual(self.utm_medium.crm_lead_count, 2)
        lead_2.action_archive()
        self.utm_medium._compute_crm_lead_count()
        self.assertEqual(self.utm_medium.crm_lead_count, 2)

    def test_action_redirect_to_quotations(self):
        self._create_sale_order(self.utm_medium)
        self._create_sale_order(self.utm_medium)
        action = self.utm_medium.action_redirect_to_quotations()
        self.assertEqual(
            action['domain'], [('medium_id', '=', self.utm_medium.id)])
        self.assertEqual(
            action['context']['default_medium_id'], self.utm_medium.id)
        self.assertIn('sale.action_quotations', action['xml_id'])

    def test_action_redirect_to_invoiced(self):
        invoice_1 = self._create_invoice(self.utm_medium)
        invoice_1.action_post()
        invoice_2 = self._create_invoice(self.utm_medium)
        invoice_2.action_post()
        action = self.utm_medium.action_redirect_to_invoiced()
        domain_ids = [d for d in action['domain'] if d[0] == 'id'][0][2]
        self.assertEqual(
            sorted(domain_ids),
            sorted([invoice_1.id, invoice_2.id]))
        self.assertIn(
            ('move_type', 'in', (
                'out_invoice', 'out_refund', 'in_invoice',
                'in_refund', 'out_receipt', 'in_receipt'
            )),
            action['domain']
        )
        self.assertFalse(action['context']['create'])
        self.assertFalse(action['context']['edit'])

    def test_action_redirect_to_leads_opportunities(self):
        self._create_lead(self.utm_medium)
        self._create_lead(self.utm_medium)
        action = self.utm_medium.action_redirect_to_leads_opportunities()
        self.assertEqual(
            action['domain'], [('medium_id', 'in', self.utm_medium.ids)])
        self.assertFalse(action['context']['create'])
        self.assertFalse(action['context']['active_test'])
        self.assertEqual(
            action['view_mode'], 'tree,kanban,graph,pivot,form,calendar')

    def test_use_leads_compute(self):
        self.utm_medium._compute_use_leads()
        use_leads = self.env.user.has_group('crm.group_use_lead')
        self.assertEqual(self.utm_medium.use_leads, use_leads)

    def test_multiple_mediums_quotation_count(self):
        medium_2 = self.env['utm.medium'].create({
            'name': 'Test Medium 2',
        })
        self._create_sale_order(self.utm_medium)
        self._create_sale_order(self.utm_medium)
        self._create_sale_order(medium_2)
        mediums = self.utm_medium | medium_2
        mediums._compute_quotation_count()
        self.assertEqual(self.utm_medium.quotation_count, 2)
        self.assertEqual(medium_2.quotation_count, 1)

    def test_multiple_mediums_invoiced_amount(self):
        medium_2 = self.env['utm.medium'].create({
            'name': 'Test Medium 2',
        })
        invoice_1 = self._create_invoice(self.utm_medium)
        invoice_1.action_post()
        invoice_2 = self._create_invoice(medium_2)
        invoice_2.action_post()
        mediums = self.utm_medium | medium_2
        mediums._compute_sale_invoiced_amount()
        self.assertEqual(self.utm_medium.invoiced_amount, 100.0)
        self.assertEqual(medium_2.invoiced_amount, 100.0)

    def test_multiple_mediums_lead_count(self):
        medium_2 = self.env['utm.medium'].create({
            'name': 'Test Medium 2',
        })
        self._create_lead(self.utm_medium)
        self._create_lead(medium_2)
        self._create_lead(medium_2)
        mediums = self.utm_medium | medium_2
        mediums._compute_crm_lead_count()
        self.assertEqual(self.utm_medium.crm_lead_count, 1)
        self.assertEqual(medium_2.crm_lead_count, 2)
