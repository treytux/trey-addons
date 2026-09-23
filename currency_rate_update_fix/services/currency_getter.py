# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
class AbstractClassError(Exception):
    def __str__(self):
        return 'Abstract Class'

    def __repr__(self):
        return 'Abstract Class'


class AbstractMethodError(Exception):
    def __str__(self):
        return 'Abstract Method'

    def __repr__(self):
        return 'Abstract Method'


class UnknowClassError(Exception):
    def __str__(self):
        return 'Unknown Class'

    def __repr__(self):
        return 'Unknown Class'


class UnsuportedCurrencyError(Exception):
    def __init__(self, value):
        self.curr = value

    def __str__(self):
        return 'Unsupported currency %s' % self.curr

    def __repr__(self):
        return 'Unsupported currency %s' % self.curr


class Currency_getter_factory():

    def register(self, class_name):
        allowed = [
            'CH_ADMIN_getter',
            'PL_NBP_getter',
            'ECB_getter',
            'GOOGLE_getter',
            'YAHOO_getter',
            'MX_BdM_getter',
            'CA_BOC_getter',
            'RO_BNR_getter',
        ]
        if class_name in allowed:
            if class_name != 'RO_BNR_getter':
                path = 'from openerp.addons.currency_rate_update.services.'
            else:
                path = 'from .'
            exec '%supdate_service_%s import %s' % (
                path, class_name.replace('_getter', ''), class_name)
            class_def = eval(class_name)
            return class_def()
        else:
            raise UnknowClassError
