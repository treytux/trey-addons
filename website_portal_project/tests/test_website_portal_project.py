# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests


@openerp.tests.common.at_install(False)
@openerp.tests.common.post_install(True)
class TestUi(openerp.tests.HttpCase):

    def test_01_website_portal_project_admin(self):
        self.phantom_js("/",
                        "openerp.Tour.run('website_portal2xx', 'test')",
                        "openerp.Tour.tours.website_portal2xx",
                        login='admin')

    # def test_02_website_portal_project_demo(self):
    #     self.phantom_js("/my/projects/",
    #                     "openerp.Tour.run('website_portal_project', 'test')",
    #                     "openerp.Tour.tours.website_portal_project",
    #                     login='demo')

    # def test_03_website_portal_project_portal(self):
    #     self.phantom_js("/my/home/",
    #                     "openerp.Tour.run('website_portal_project', 'test')",
    #                     "openerp.Tour.tours.website_portal_project",
    #                     login='portal')
