###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestQualityPartnerLog(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })

    def test_add_quality_partner_log(self):
        self.assertFalse(self.partner.qualification_log_ids)
        self.partner.price_quality = '3_good'
        self.assertEquals(len(self.partner.qualification_log_ids), 1)
        self.assertEquals(
            self.partner.qualification_log_ids.price_quality, '3_good')
        self.assertEquals(
            self.partner.qualification_log_ids.service_quality, '2_regular')
        self.assertEquals(
            self.partner.qualification_log_ids.attencion_quality, '2_regular')
        self.assertEquals(
            self.partner.qualification_log_ids.partner_quality, 0)
        self.assertEquals(
            self.partner.qualification_log_ids.qualification_date, 0)
        self.partner.service_quality = '3_good'
        self.assertEquals(len(self.partner.qualification_log_ids), 2)
        self.assertEquals(
            self.partner.qualification_log_ids[-1].price_quality, '3_good')
        self.assertEquals(
            self.partner.qualification_log_ids[-1].service_quality, '3_good')
        self.assertEquals(
            self.partner.qualification_log_ids[-1].attencion_quality,
            '2_regular')
        self.assertEquals(
            self.partner.qualification_log_ids[-1].partner_quality, 0)
        self.assertEquals(
            self.partner.qualification_log_ids[-1].qualification_date, 0)
        self.partner.attencion_quality = '3_good'
        self.assertEquals(len(self.partner.qualification_log_ids), 3)
        self.assertEquals(
            self.partner.qualification_log_ids[-1].price_quality, '3_good')
        self.assertEquals(
            self.partner.qualification_log_ids[-1].service_quality, '3_good')
        self.assertEquals(
            self.partner.qualification_log_ids[-1].attencion_quality, '3_good')
        self.assertEquals(
            self.partner.qualification_log_ids[-1].partner_quality, 0)
        self.assertEquals(
            self.partner.qualification_log_ids[-1].qualification_date, 0)

    def test_no_add_quality_partner_log(self):
        self.assertFalse(self.partner.qualification_log_ids)
        self.partner.name = 'New name'
        self.assertFalse(self.partner.qualification_log_ids)

    def test_onchange_quality(self):
        self.assertEquals(self.partner.price_quality, '2_regular')
        self.assertEquals(self.partner.service_quality, '2_regular')
        self.assertEquals(self.partner.attencion_quality, '2_regular')
        self.partner.write({
            'price_quality': '3_good',
            'service_quality': '3_good',
            'attencion_quality': '3_good',
        })
        self.partner.onchange_quality()
        self.assertEquals(self.partner.price_quality, '3_good')
        self.assertEquals(self.partner.service_quality, '3_good')
        self.assertEquals(self.partner.attencion_quality, '3_good')
        self.assertEquals(self.partner.partner_quality, 9)
        today = fields.Date.today()
        self.assertEquals(self.partner.qualification_date, today)
