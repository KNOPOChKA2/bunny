#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       bunny.py
#       
#       Copyright 2011 Parker Thompson <w.parker.thompson@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#     

from AEScrypt import *
#from configure import *
from SendRec import *
from Templates import *
from TrafficModel import *
from config import *

class Bunny:
	"""
	
	High level send and recive for wrapping all the lower function of bunny in paranoid mode.
	
	"""
		
	def __init__(self):
		"""
		
		Setup and build the bunny model
		
		"""
		
		self.inandout = SendRec()
		self.cryptor = AEScrypt()
		self.model = TrafficModel()
		
	def sendBunny(self, packet):
		"""
		
		Send a Bunny (paranoid) packet
		
		"""
		
		packet = self.cryptor.encrypt(packet)
		if DEBUG:
			print "CypherText: " + binascii.hexlify(packet)
			print "blocks: " + binascii.hexlify(packet[16:18])
		
		while ( len(packet) != 0 ):
			entry = self.model.getEntryFrom(self.model.type_ranges)
			try:
				outpacket = entry[2].makePacket(packet[:entry[3]])
				if DEBUG:
					print "Sending with: %s" % self.model.rawToType(entry[0])
					print "length: " + str(len(outpacket))
				
			except AttributeError:
				continue
			packet = packet[entry[3]:]
			self.inandout.sendPacket(outpacket)
			time.sleep(0.07)
			
	def recvBunny(self):
		"""
		
		Read and decode loop for bunny, raises a TimeoutWarning if it times out.
		
		"""

		
		blockget = False
		decoded = ""
		
		while True:
			# declare / clear the type array.
			type = []
			
			try:						
				encoded = self.inandout.recPacket_timeout(self.model.FCS)
			except TimeoutWarning:
				blockget = False
				decoded = ""
				continue
			
			if DEBUG:
				print "\nHit packet"
			
			if DEBUG:
				print "Type: %s\t Raw: %s" % (binascii.hexlify(encoded[0:1]), self.model.rawToType(encoded[0:1]))
			
			for entry in self.model.type_ranges:
				if entry[0] == encoded[0:1]:
					if entry[3] > 0:
						# check so that the injectable length is over 0
						type = entry
						break
						
			if len(type) < 2:
				if DEBUG:
					print "Packet not in templates"
				continue
			
			# decode the bunny packet
			temp = type[2].decode(encoded)
			if DEBUG:
				print "CypherText: " + binascii.hexlify(temp)
			
			if temp is False:
				if DEBUG:
					print "decoding fail"
				continue
			else:
				decoded_len = len(decoded)
				if decoded_len < 18:
					decoded = decoded + temp
				else:
					if blockget == False:
						blocks, = struct.unpack("H", decoded[16:18])
						
						if DEBUG:
							print "blocks: " + str(blocks)
						blockget = True
						decoded = decoded + temp
						decoded_len = len(decoded)
					elif decoded_len < (32*blocks + 18):
						decoded = decoded + temp
						decoded_len = len(decoded)
					if decoded_len >= (32*blocks + 18):
						# might be redundant
						if DEBUG:
							print "Ending the loop"
						return self.cryptor.decrypt(decoded)
