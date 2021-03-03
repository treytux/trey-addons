# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _
from openerp.tests import common
import base64
import os


class ImportSaleCreditLimit(common.TransactionCase):

    def setUp(self):
        super(ImportSaleCreditLimit, self).setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner test 01',
            'vat': 'ESA28425270',
            'credit_limit': 100,
        })
        self.partner_02 = self.env['res.partner'].create({
            'name': 'Partner test 02',
            'vat': 'ESA28017895',
            'credit_limit': 200,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def test_import_credit_limit_ok(self):
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].with_context(
            lang='en_US').create({'ffile': file})
        wizard.button_simulation()
        self.assertEquals(wizard.log_simulation, '')
        wizard.button_done()
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 01 with vat '
            'A-28425270: 100.0 => 120000.'), wizard.log_write)
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 02 with vat '
            'A28017895: 200.0 => 150000.'), wizard.log_write)
        self.assertEquals(self.partner_01.credit_limit, 120000)
        self.assertEquals(self.partner_02.credit_limit, 150000)

    def test_import_credit_limit_vat_not_exists(self):
        fname = self.get_sample('sample_vat_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].with_context(
            lang='en_US').create({'ffile': file})
        wizard.button_simulation()
        self.assertIn(_(
            '\nNo partner was found with the vat \'B20435301\'.'),
            wizard.log_simulation)
        wizard.button_done()
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 01 with vat '
            'A-28425270: 100.0 => 120000.'), wizard.log_write)
        self.assertIn(_(
            '\nNo partner was found with the vat \'B20435301\'.'),
            wizard.log_write)
        self.assertEquals(self.partner_01.credit_limit, 120000)
        self.assertEquals(self.partner_02.credit_limit, 200)

    def test_import_credit_limit_vat_duply(self):
        self.partner_03 = self.env['res.partner'].create({
            'name': 'Partner test 03',
            'vat': 'ESA28017895',
            'credit_limit': 400,
        })
        self.assertEquals(self.partner_02.vat, self.partner_03.vat)
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].with_context(
            lang='en_US').create({'ffile': file})
        wizard.button_simulation()
        self.assertIn(_(
            'There is more than one partner with the vat \'A28017895\', check '
            'it.'), wizard.log_simulation)
        wizard.button_done()
        self.assertIn(_(
            'There is more than one partner with the vat \'A28017895\', check '
            'it.'), wizard.log_write)
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 01 with vat '
            'A-28425270: 100.0 => 120000.'), wizard.log_write)
        self.assertEquals(self.partner_01.credit_limit, 120000)
        self.assertEquals(self.partner_02.credit_limit, 200)

    def test_import_credit_limit_vat_duply_with_partner_name_col_ok(self):
        self.partner_03 = self.env['res.partner'].create({
            'name': 'Partner test 03',
            'vat': 'ESA28017895',
            'credit_limit': 400,
        })
        self.assertEquals(self.partner_02.vat, self.partner_03.vat)
        fname = self.get_sample('sample_with_partner_name_col_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].with_context(
            lang='en_US').create({'ffile': file})
        wizard.button_simulation()
        self.assertEquals(wizard.log_simulation, '')
        wizard.button_done()
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 01 with vat '
            'A-28425270: 100.0 => 120000.'), wizard.log_write)
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 03 with vat '
            'A28017895: 400.0 => 150000.'), wizard.log_write)
        self.assertEquals(self.partner_01.credit_limit, 120000)
        self.assertEquals(self.partner_02.credit_limit, 200)
        self.assertEquals(self.partner_03.credit_limit, 150000)

    def test_import_credit_limit_vat_duply_with_partner_name_col_bad(self):
        self.partner_03 = self.env['res.partner'].create({
            'name': 'Partner test 03',
            'vat': 'ESA28017895',
            'credit_limit': 400,
        })
        self.assertEquals(self.partner_02.vat, self.partner_03.vat)
        fname = self.get_sample('sample_with_partner_name_col_bad.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].with_context(
            lang='en_US').create({'ffile': file})
        wizard.button_simulation()
        self.assertIn(_(
            '\nThere is more than one partner that has the vat \'A28017895\' '
            'assigned. We searched by name but no partner was found with vat '
            '\'A28017895\' and name \'Partner test xx\'.'),
            wizard.log_simulation)
        wizard.button_done()
        self.assertIn(_(
            '\nCredit limit updated for partner Partner test 01 with vat '
            'A-28425270: 100.0 => 120000.'), wizard.log_write)
        self.assertIn(_(
            '\nThere is more than one partner that has the vat \'A28017895\' '
            'assigned. We searched by name but no partner was found with vat '
            '\'A28017895\' and name \'Partner test xx\'.'),
            wizard.log_write)
        self.assertEquals(self.partner_01.credit_limit, 120000)
        self.assertEquals(self.partner_02.credit_limit, 200)
        self.assertEquals(self.partner_03.credit_limit, 400)

    def test_import_credit_limit_bad_header_col1(self):
        fname = self.get_sample('sample_bad_header_col1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].create({'ffile': file})
        self.assertRaises(Exception, wizard.button_simulation)

    def test_import_credit_limit_bad_header_col2(self):
        fname = self.get_sample('sample_bad_header_col2.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].create({'ffile': file})
        self.assertRaises(Exception, wizard.button_simulation)

    def test_import_credit_limit_bad_no_vat(self):
        fname = self.get_sample('sample_bad_no_vat.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].create({'ffile': file})
        self.assertRaises(Exception, wizard.button_simulation)

    def test_import_credit_limit_bad_no_credit(self):
        fname = self.get_sample('sample_bad_no_credit.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].create({'ffile': file})
        self.assertRaises(Exception, wizard.button_simulation)

    def test_import_credit_limit_bad_amount_not_float(self):
        fname = self.get_sample('sample_bad_amount_not_float.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.credit_limit'].create({'ffile': file})
        self.assertRaises(Exception, wizard.button_simulation)
