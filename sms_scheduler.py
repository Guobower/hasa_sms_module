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
from osv import osv, fields
from datetime import datetime
import time
from clickatell.rest import Rest
from datetime import datetime, timedelta
import logging
import re

class smartcab_sms_scheduler(osv.osv):
	_name="smartcab.sms.scheduler"

	_columns = {
	}

	_defaults = {
	}
	
	def _send_sms(self, cr, uid, *args):
		_logger = logging.getLogger(__name__)
		_logger.error("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
		now = datetime.now()
		today = datetime.strptime(str(now.day) + '-' + str(now.month) + '-' + str(now.year), '%d-%m-%Y') + timedelta(days=1)
		tomorrow = today.strftime('%d-%m-%Y 00:00:00')
		today = today + timedelta(days=1)
		aftertomorrow = today.strftime('%d-%m-%Y 00:00:00')

		meeting_obj = self.pool.get('crm.meeting')

		sender = args[0]

		meetings = meeting_obj.search(cr, uid,[('date','>',tomorrow), ('date', '<', aftertomorrow)])
		for meeting in meeting_obj.browse(cr, uid, meetings):
			for partner in meeting.partner_ids:
				if partner.mobile:
					tel = partner.mobile.replace(' ','')
					if re.match('^\+417[0-9]{8}$', tel) != None:
						_logger.info(tel)
					elif re.match('^07[0-9]{8}$', tel) != None:
						_logger.info('+41' + tel[1:])
						tel = '+41' + tel[1:]
					elif re.match('^7[0-9]{8}$', tel) != None:
						_logger.info('+41' + tel)
						tel = '+41' + tel
					elif re.match('^00417[0-9]{8}$', tel) != None:
						_logger.info('+' + tel[2:])
						tel = '+' + tel[2:]
					
					message = 'Bonjour, ceci est un message automatique pour vous rappeler que vous avez rendez-vous demain à ' + meeting.date[11:-3].replace(':', 'h') + ' avec M.' + sender
					response = {'error':False}	
	
					_logger.info(message)
	
					#clickatell = Rest(KEY); 
					#response = clickatell.sendMessage(['+41792047033'], "Test", extra={'from':'Hasa'})
					
					if response['error']:
						_logger.info(u'SMS envoyé à ' + partner.first_name + ' ' + partner.last_name + ' - Resultat : Erreur - ' + response['errorCode'])
					else:
						_logger.info(u'SMS envoyé à ' + partner.first_name + ' ' + partner.last_name + u' - Resultat : Succès')

smartcab_sms_scheduler()
