# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import math
import re


def ean_checksum(eancode):
    if len(eancode) != 13:
        return -1
    oddsum = 0
    evensum = 0
    total = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]
    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum
    check = int(10 - math.ceil(total % 10.0)) % 10
    return check


def check_ean(eancode):
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except Exception:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


def sanitize_ean13(ean13):
    if not ean13:
        return "0000000000000"
    ean13 = re.sub("[A-Za-z]", "0", ean13)
    ean13 = re.sub("[^0-9]", "", ean13)
    ean13 = ean13[:13]
    if len(ean13) < 13:
        ean13 = ean13 + '0' * (13-len(ean13))
    return ean13[:-1] + str(ean_checksum(ean13))
