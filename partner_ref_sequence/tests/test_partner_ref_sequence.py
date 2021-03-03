###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerRefSequence(TransactionCase):

    def test_partner_ref_sequence(self):
        sequence = self.env.ref('partner_ref_sequence.partner_ref_sequence')
        self.assertTrue(sequence)
        number = sequence.number_next_actual
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.assertEquals(partner.ref, str(number).zfill(6))
        sequence.number_next_actual *= 10
        number2 = sequence.number_next_actual
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.assertEquals(partner.ref, str(number2).zfill(6))
        sequence.number_next_actual = number + 1
