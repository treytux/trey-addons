# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import re
import openerp.addons.auth_signup.controllers.main as main


class AuthSignupHome(main.AuthSignupHome):
    def _is_email(self, email):
        EMAIL_REGEX = ("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]"
                       "{1,3})(\\]?)$")
        return True if re.match(EMAIL_REGEX, email) is not None else False

    def do_signup(self, qcontext):
        assert self._is_email(qcontext.get('login')), "Invalid email."
        super(AuthSignupHome, self).do_signup(qcontext)
