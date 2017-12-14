# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp.tests import common


class test_security_rules(common.TransactionCase):

    def setUp(self):
        super(test_security_rules, self).setUp()

        cr, uid = self.cr, self.uid
        User = self.registry('res.users')

        self.utid = User.create(cr, uid, {
            'name': 'test',
            'login': 'test@test.com',
            'password': 'test',
        })

        groups_ids = [
            'group_partner_customer_created', 'group_partner_customer_created',
            'group_partner_customer_salesman_rule', 'group_product_procurement'
        ]
        self.groups = {}
        for group_id in groups_ids:
            ids = self.registry('ir.model.data').get_object_reference(
                cr, uid, 'security', group_id)
            self.groups[group_id] = ids and ids[1] or False

        Partner = self.registry('res.partner')
        Partner.create(cr, self.utid, {
            'name': 'Usuario creado para las pruebas',
            'email': 'test@localhost',
            'is_company': True,
        }, context=None)
