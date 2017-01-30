#!/usr/bin/python3
#
# Copyright (C) 2017  Jochen Sprickerhof
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from argparse import ArgumentParser, FileType
from getpass import getpass
from netrc import netrc
from sys import stdout

from vobject import vCard
from vobject.vcard import Address, Name
from exchangelib import Account, Credentials, Configuration, DELEGATE, NTLM

def to_vcard(contact):
    card = vCard()

    card.add('uid').value = contact.item_id
    card.add('fn').value = contact.file_as
    card.add('n').value = Name(family=contact.surname or '',
                               given=contact.given_name or '',
                               additional=contact.middle_name or '')

    if contact.job_title:
        card.add('title').value = contact.job_title

    card.add('org').value = (contact.company_name or '',
                             contact.department or '',
                             contact.office or '')

    for email in contact.email_addresses or []:
        card.add('email').value = email.email

    for attachment in contact.attachments or []:
        if attachment.is_contact_photo:
            photo = card.add('photo')
            if attachment.content_type == 'image/jpeg':
                photo.type_param = 'jpeg'
            photo.encoding_param = 'b'
            photo.value = attachment.content

    for address in contact.physical_addresses or []:
        card.add('adr').value = Address(street=address.street or '',
                                        city=address.city or '',
                                        region=address.state or '',
                                        code=address.zipcode or '',
                                        country=address.country or '')

    for phone in contact.phone_numbers or []:
        tel = card.add('tel')
        tel.value = phone.phone_number
        if phone.label == 'BusinessPhone':
            tel.type_param = 'work'
        elif phone.label == 'HomePhone':
            tel.type_param = 'home'
        elif phone.label == 'MobilePhone':
            tel.type_param = 'cell'

    return card

def main():
    """Command line tool to export Exchange contacts to vCard"""

    parser = ArgumentParser(description='Convert from Exchange to vCard.')
    parser.add_argument('-e', '--email', required=True, help='The email address for the Exchange server')
    parser.add_argument('-p', '--password', help='The password for the Exchange server')
    parser.add_argument('-s', '--server', required=True, help='the server name to connect to')
    parser.add_argument('-u', '--username', help='The username for the Exchange server')
    parser.add_argument('outfile', nargs='?', type=FileType('w'), default=stdout, help='Output vCard file (default: stdout)')
    args = parser.parse_args()

    if args.username and args.password:
        username = args.username
        password = args.password
    else:
        try:
            (username, _, password) = netrc().authenticators(args.server)
        except (IOError, TypeError):
            if not args.username:
                print('exchange: Error, argument -u/--username or netrc is required')
                return 1
            username = args.username
            try:
                from keyring import get_password
                password = get_password(args.server, username)
            except ImportError:
                password = None
            if not password:
                password = getpass()

    config = Configuration(server=args.server,
                           credentials=Credentials(username=username,
                                                   password=password),
                           auth_type=NTLM)

    account = Account(primary_smtp_address=args.email,
                      config=config,
                      access_type=DELEGATE)

    cards = [to_vcard(contact) for contact in account.contacts.all()]
    args.outfile.write('\r\n'.join([c.serialize() for c in cards]))

if __name__ == '__main__':
    main()
