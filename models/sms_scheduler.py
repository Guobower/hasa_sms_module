# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 HASA (http://www.hasa.ch) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from odoo import fields, models, api, exceptions
import time
from datetime import datetime, timedelta
from dateutil import tz
import logging
import re
import requests
import json

_logger = logging.getLogger(__name__)


clickatellapi_url = 'https://api.clickatell.com/rest/message'

class smartcab_sms_scheduler(models.Model):
	_name="smartcab.sms.scheduler"
	
	def _send_message(self, headers, text, to, sender_id):
		values = {
			"from": sender_id,
			"text": text,
			"to": [to],
		}
		return requests.post(clickatellapi_url, 
					json=values, 
					headers=headers)

	def parse_mobile_number(self,tel_number):
		if re.match('^\+417[0-9]{8}$', tel_number) != None:
			return tel_number
		if re.match('^417[0-9]{8}$', tel_number) != None:
			return '+' + tel_number
		elif re.match('^07[0-9]{8}$', tel_number) != None:
			return '+41' + tel_number[1:]
		elif re.match('^7[0-9]{8}$', tel_number) != None:
			return '+41' + tel_number
		elif re.match('^00417[0-9]{8}$', tel_number) != None:
			return '+' + tel_number[2:]
		else:
			_logger.error("Invalid patient number : {}".format(tel_number))
			return 'error '+ tel_number

	@api.model
	def _send_sms(self):
		now = datetime.now()
		today = datetime.strptime(str(now.day) + '-' + str(now.month) + '-' + str(now.year), '%d-%m-%Y') + timedelta(days=1)
		tomorrow = today.strftime('%Y-%m-%d %H:%M:%S')
		today = today + timedelta(days=1)
		aftertomorrow = today.strftime('%Y-%m-%d %H:%M:%S')

		calendar_event_obj = self.env['calendar.event']
		company_id = self.env.user.company_id
		if not company_id.clickatell_key:
			_logger.warning("There's no clickatell key for company {}".format(company_id.id))
			return

		headers = {
			"Authorization": "bearer " + company_id.clickatell_key,
			"Content-Type": "application/json",
			"X-Version": "1",
			"Accept": "application/json"
		}
		meetings = calendar_event_obj.search([('start_datetime','>',tomorrow), ('start_datetime', '<', aftertomorrow)])
		for meeting in meetings:
			if meeting.partner_id.mobile and not meeting.partner_id.disable_sms:

				tel = meeting.partner_id.mobile.replace(' ','')
				tel_number = self.parse_mobile_number(tel)
				
				if 'error' not in tel_number:
					from_zone = tz.tzutc()
					to_zone = tz.gettz('Europe/Paris')
					utc = datetime.strptime( meeting.start_datetime,'%Y-%m-%d %H:%M:%S').replace(tzinfo=from_zone)
					central = utc.astimezone(to_zone)
					time_rdv = central.strftime('%H:%M')
					date_rdv = central.strftime('%d-%m-%Y')

					message = u'Bonjour, ceci est un message automatique pour vous rappeler que vous avez rendez-vous demain à ' + time_rdv + ' avec ' + meeting.praticien_id.name
					
					response = self._send_message(headers, message, tel_number, "Smartcab")
					response_json = json.loads(response.text)

					if response.status_code != "200" and response_json["data"]["message"][0]["accepted"] == True:
						_logger.info(u'SMS envoyé à ' + meeting.partner_id.first_name + ' ' + meeting.partner_id.last_name + ' - Resultat : Erreur - ' + response.text)
					else:
						_logger.info(u'SMS envoyé à ' + meeting.partner_id.first_name + ' ' + meeting.partner_id.last_name + u' - Resultat : Succès')