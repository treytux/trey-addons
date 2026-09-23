###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase


class TestMod349ShippingPartner(TestL10nEsAeatModBase):

    taxes_sale = {
        'S_IVA0_IC': (2400, 0),
    }
    taxes_purchase = {}

    def _shipping_partner(self, name, vat, country_xmlid='base.be'):
        return self.env['res.partner'].create({
            'name': name,
            'vat': vat,
            'country_id': self.env.ref(country_xmlid).id,
        })

    def _create_report(self, date_start='2017-01-01', date_end='2017-03-31'):
        return self.env['l10n.es.aeat.mod349.report'].with_user(
            self.account_manager
        ).create({
            'name': '3490000000001',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'statement_type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': date_start,
            'date_end': date_end,
        })

    def test_invoice_record_uses_shipping_partner(self):
        shipping_partner = self._shipping_partner(
            'Shipping company', 'BE0411905847')
        invoice = self._invoice_sale_create(
            '2017-01-01', {'partner_shipping_id': shipping_partner.id})
        report = self._create_report()
        report.button_calculate()
        self.assertEqual(len(report.partner_record_ids), 1)
        record = report.partner_record_ids
        self.assertEqual(record.partner_id, shipping_partner)
        self.assertEqual(record.partner_vat, shipping_partner.vat)
        self.assertEqual(record.country_id, shipping_partner.country_id)
        self.assertEqual(record.record_detail_ids.move_id, invoice)

    def test_invoice_record_falls_back_to_invoice_partner(self):
        self.customer.write({
            'vat': 'BE0411905847',
            'country_id': self.env.ref('base.be').id,
        })
        self._invoice_sale_create('2017-01-01')
        report = self._create_report()
        report.button_calculate()
        self.assertEqual(len(report.partner_record_ids), 1)
        record = report.partner_record_ids
        self.assertEqual(record.partner_id, self.customer)
        self.assertEqual(record.partner_vat, self.customer.vat)
        self.assertEqual(record.country_id, self.customer.country_id)

    def test_invoice_records_group_by_shipping_partner_and_operation(self):
        shipping_partner = self._shipping_partner(
            'Shipping company', 'BE0411905847')
        self._invoice_sale_create(
            '2017-01-01', {'partner_shipping_id': shipping_partner.id})
        self._invoice_sale_create(
            '2017-01-02', {'partner_shipping_id': shipping_partner.id})
        report = self._create_report()
        report.button_calculate()
        self.assertEqual(len(report.partner_record_ids), 1)
        record = report.partner_record_ids
        self.assertEqual(record.partner_id, shipping_partner)
        self.assertEqual(len(record.record_detail_ids), 2)
        self.assertEqual(record.total_operation_amount, 4800)

    def test_refund_record_uses_refund_shipping_partner(self):
        original_shipping_partner = self._shipping_partner(
            'Original shipping company', 'BE0411905847')
        refund_shipping_partner = self._shipping_partner(
            'Refund shipping company', 'BG0000100159', 'base.bg')
        invoice = self._invoice_sale_create(
            '2017-01-01', {'partner_shipping_id': original_shipping_partner.id})
        refund = self._invoice_refund(invoice, '2017-04-01')
        refund.partner_shipping_id = refund_shipping_partner
        report = self._create_report('2017-04-01', '2017-06-30')
        report.period_type = '2T'
        report.year = 2017
        report.button_calculate()
        self.assertEqual(len(report.partner_refund_ids), 1)
        refund_record = report.partner_refund_ids
        self.assertEqual(refund_record.partner_id, refund_shipping_partner)
        self.assertEqual(
            refund_record.partner_vat, refund_shipping_partner.vat)
        self.assertEqual(
            refund_record.country_id, refund_shipping_partner.country_id)
        self.assertEqual(refund_record.refund_detail_ids.move_id, refund)
        self.assertEqual(refund_record.total_origin_amount, 2400)

    def test_recalculating_report_does_not_duplicate_shipping_records(self):
        shipping_partner = self._shipping_partner(
            'Shipping company', 'BE0411905847')
        self._invoice_sale_create(
            '2017-01-01', {'partner_shipping_id': shipping_partner.id})
        report = self._create_report()
        report.button_calculate()
        report.button_calculate()
        self.assertEqual(len(report.partner_record_ids), 1)
        self.assertEqual(len(report.partner_record_detail_ids), 1)
        self.assertEqual(
            report.partner_record_ids.partner_id, shipping_partner)
