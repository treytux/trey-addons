import json
from datetime import datetime

from bs4 import BeautifulSoup
from markupsafe import Markup
from odoo import models


class Event(models.Model):
    _inherit = 'event.event'

    def get_event_location(self):
        has_online_tag = any('online' in tag.name.lower() for tag in self.tag_ids)
        has_address = bool(self.address_id)
        if has_online_tag and has_address:
            event_mode = 'https://schema.org/MixedEventAttendanceMode'
            location_data = [
                {
                    '@type': 'VirtualLocation',
                    'url': self.website_url or '',
                },
                {
                    '@type': 'Place',
                    'name': self.address_id.name,
                    'address': {
                        '@type': 'PostalAddress',
                        'streetAddress': self.address_id.street if self.address_id
                        else '',
                        'addressLocality': self.address_id.city if self.address_id
                        else '',
                        'postalCode': self.address_id.zip if self.address_id
                        else '',
                        'addressRegion': self.address_id.state_id.code
                        if self.address_id and self.address_id.state_id else '',
                        'addressCountry': self.address_id.country_id.code
                        if self.address_id and self.address_id.country_id else '',
                    },
                },
            ]
        elif has_online_tag:
            event_mode = 'https://schema.org/OnlineEventAttendanceMode'
            location_data = {
                '@type': 'VirtualLocation',
                'url': self.website_url or '',
            }
        else:
            event_mode = 'https://schema.org/OfflineEventAttendanceMode'
            location_data = {
                '@type': 'Place',
                'name': self.address_id.name,
                'address': {
                    '@type': 'PostalAddress',
                    'streetAddress': self.address_id.street if self.address_id
                    else '',
                    'addressLocality': self.address_id.city if self.address_id
                    else '',
                    'postalCode': self.address_id.zip if self.address_id else '',
                    'addressRegion': self.address_id.state_id.code
                    if self.address_id and self.address_id.state_id else '',
                    'addressCountry': self.address_id.country_id.code
                    if self.address_id and self.address_id.country_id else '',
                },
            }
        return event_mode, location_data

    def event_schema_get(self):
        self.ensure_one()
        tickets = self.event_ticket_ids
        if tickets:
            cheapest_ticket = min(tickets, key=lambda t: t.price)
            price = cheapest_ticket.price
            valid_from = cheapest_ticket.start_sale_datetime or self.date_begin
        else:
            price = 0.0
            valid_from = self.date_begin
        now = datetime.now()
        if tickets and all(t.is_sold_out for t in tickets):
            availability = 'https://schema.org/SoldOut'
        elif tickets and all(t.start_sale_datetime and t.start_sale_datetime > now
                             for t in tickets):
            availability = 'https://schema.org/PreOrder'
        else:
            availability = 'https://schema.org/InStock'
        event_mode, location_data = self.get_event_location()
        return Markup(json.dumps({
            '@context': 'https://schema.org',
            '@type': 'Event',
            'name': self.name,
            'startDate': self.date_begin.isoformat(),
            'endDate': self.date_end.isoformat(),
            'eventAttendanceMode': event_mode,
            'eventStatus': 'https://schema.org/EventScheduled',
            'location': location_data,
            'image': [
                self._get_background(width=800, height=800),
                self._get_background(width=800, height=600),
                self._get_background(width=800, height=450),
            ],
            'description': BeautifulSoup(
                self.description, 'html.parser'
            ).get_text().strip()if self.description else '',
            'offers': {
                '@type': 'Offer',
                'url': self.website_url or '',
                'price': price,
                'priceCurrency': self.company_id.currency_id.name or 'USD',
                'availability': availability,
                'validFrom': valid_from.isoformat(),
            },
            'organizer': {
                '@type': 'Organization',
                'name': self.organizer_id.name or '',
                'url': f'/author/profile/{self.organizer_id.id}'
            },
        }, indent=4))
