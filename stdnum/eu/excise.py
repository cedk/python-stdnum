# excise.py - functions for handling EU Excise numbers
# coding: utf-8
#
# Copyright (C) 2023 Cédric Krier
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

"""European Excise Number

The excise duty identification number assigned to businesses authorised to
operate with excise goods (e.g. alcohol, tobacco, energy products, etc.).

The number is issued by the national customs or tax authority of the Member
State where the business is established. The number consists of a two-letter
country code followed by up to 13 alphanumeric characters.

More information:

* https://ec.europa.eu/taxation_customs/dds2/seed/

>>> validate('LU 987ABC')
'LU00000987ABC'
"""

from __future__ import annotations

from stdnum.eu.vat import MEMBER_STATES
from stdnum.exceptions import *
from stdnum.util import NumberValidationModule, clean, get_cc_module, get_soap_client


_country_modules = dict()

seed_wsdl = 'https://ec.europa.eu/taxation_customs/dds2/seed/services/excise/verification?wsdl'
"""The WSDL URL of the System for Exchange of Excise Data (SEED)."""


def _get_cc_module(cc: str) -> NumberValidationModule | None:
    """Get the Excise number module based on the country code."""
    cc = cc.lower()
    if cc not in MEMBER_STATES:
        raise InvalidComponent()
    if cc not in _country_modules:
        _country_modules[cc] = get_cc_module(cc, 'excise')
    return _country_modules[cc]


def compact(number: str) -> str:
    """Convert the number to the minimal representation. This strips the number
    of any valid separators and removes surrounding whitespace."""
    number = clean(number, ' ').upper().strip()
    if len(number) < 13:
        number = number[:2] + number[2:].zfill(11)
    return number


def validate(number: str) -> str:
    """Check if the number is a valid Excise number."""
    number = compact(number)
    if len(number) != 13:
        raise InvalidLength()
    module = _get_cc_module(number[:2])
    if module:
        module.validate(number)
    return number


def is_valid(number: str) -> bool:
    """Check if the number is a valid excise number."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False


def check_seed(
        number: str,
        timeout: float = 30,
) -> dict[str, Any]:  # pragma: no cover (not part of normal test suite)
    """Query the online European Commission System for Exchange of Excise Data
    (SEED) for validity of the provided number. Note that the service has
    usage limitations (see the VIES website for details). The timeout is in
    seconds. This returns a dict-like object."""
    number = compact(number)
    client = get_soap_client(seed_wsdl, timeout)
    return client.verifyExcise(number)  # type: ignore[no-any-return]
