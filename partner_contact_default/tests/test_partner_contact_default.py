###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerDefaultContact(TransactionCase):

    def test_partner_default(self):
        partner = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Partner Test'))
        contact_1 = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact 1',
            parent_id=partner.id))
        contact_2 = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact 2',
            parent_id=partner.id))
        contact_3 = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact 3',
            parent_id=partner.id))
        self.assertEquals(partner.is_default, False)
        self.assertEquals(contact_1.is_default, False)
        self.assertEquals(contact_2.is_default, False)
        self.assertEquals(contact_3.is_default, False)
        partners = self.env['res.partner'].search([
            ('parent_id', '=', partner.id),
            ('name', 'ilike', '[TEST-KEY]')])
        self.assertEquals(len(partners), 3)
        self.assertEquals(partners[0].id, contact_1.id)
        contact_2.is_default = True
        self.assertEquals(partner.is_default, False)
        self.assertEquals(contact_1.is_default, False)
        self.assertEquals(contact_2.is_default, True)
        self.assertEquals(contact_3.is_default, False)
        partners = self.env['res.partner'].search([
            ('parent_id', '=', partner.id),
            ('name', 'ilike', '[TEST-KEY]')])
        self.assertEquals(len(partners), 3)
        self.assertEquals(partners[0].id, contact_2.id)
        contact_3.is_default = True
        self.assertEquals(partner.is_default, False)
        self.assertEquals(contact_1.is_default, False)
        self.assertEquals(contact_2.is_default, False)
        self.assertEquals(contact_3.is_default, True)
        partners = self.env['res.partner'].search([
            ('parent_id', '=', partner.id),
            ('name', 'ilike', '[TEST-KEY]')])
        self.assertEquals(len(partners), 3)
        self.assertEquals(partners[0].id, contact_3.id)

    def test_partner_type_default(self):
        partner = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Partner Test'))
        contact_delivery = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact Delivery',
            type='delivery',
            is_default=True,
            parent_id=partner.id))
        contact_invoice = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact Invoice',
            type='invoice',
            is_default=True,
            parent_id=partner.id))
        contact_contact = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact Contact',
            type='contact',
            is_default=True,
            parent_id=partner.id))
        contact_pivot = self.env['res.partner'].create(dict(
            name='[TEST-KEY] Contact Pivot',
            type='other',
            is_default=True,
            parent_id=partner.id))
        self.assertEquals(partner.is_default, False)
        self.assertEquals(contact_delivery.is_default, True)
        self.assertEquals(contact_invoice.is_default, True)
        self.assertEquals(contact_contact.is_default, True)
        self.assertEquals(contact_pivot.is_default, True)
        contact_pivot.type = 'delivery'
        self.assertEquals(partner.is_default, False)
        self.assertEquals(contact_pivot.is_default, True)
        self.assertEquals(contact_delivery.is_default, False)
        self.assertEquals(contact_invoice.is_default, True)
        self.assertEquals(contact_contact.is_default, True)
        contact_pivot.type = 'invoice'
        self.assertEquals(partner.is_default, False)
        self.assertEquals(contact_delivery.is_default, False)
        self.assertEquals(contact_invoice.is_default, False)
        self.assertEquals(contact_contact.is_default, True)
