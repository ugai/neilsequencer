#encoding: latin-1

# Neil
# Modular Sequencer
# Copyright (C) 2006,2007,2008 The Neil Development Team
#
# This program is free software; you can redistribute it and/or
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
Contains dialogs related to controller enumeration and pick up.
"""

import sys, os
from gi.repository import GObject, Gtk
import zzub
import webbrowser

import neil.com as com
from .utils import prepstr, buffersize_to_latency, filepath, error, add_scrollbars, new_listview
from . import utils
import config
from . import common
from .common import MARGIN, MARGIN2, MARGIN3

class SelectControllerDialog(Gtk.Dialog):
	"""
	Dialog that records a controller from keyboard input.
	"""
	def __init__(self, parent=None):
		Gtk.Dialog.__init__(self,
			"Add Controller",
			parent and parent.get_toplevel(),
			Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
			None
		)
		vbox = Gtk.VBox()
		lsizer = Gtk.VBox(False, MARGIN)
		vbox.set_border_width(MARGIN2)
		vbox.set_spacing(MARGIN)
		label = Gtk.Label("Move a control on your MIDI device to pick it up.")
		label.set_alignment(0, 0.5)
		lsizer.pack_start(label, expand=False)
		sg = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
		def make_row(name):
			row = Gtk.HBox(False, MARGIN)
			c1 = Gtk.Label()
			c1.set_markup('<b>%s</b>' % name)
			c1.set_alignment(1, 0.5)
			c2 = Gtk.Label()
			c2.set_alignment(0, 0.5)
			sg.add_widget(c1)
			row.pack_start(c1, expand=False)
			row.pack_start(c2)
			lsizer.pack_start(row, expand=False)
			return c2
		self.controllerlabel = make_row("Controller")
		self.channellabel = make_row("Channel")
		self.valuelabel = make_row("Value")
		self.btnok = self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
		self.btncancel = self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
		vbox.pack_start(lsizer, expand=False)
		hsizer = Gtk.HBox(False, MARGIN)
		self.namelabel = Gtk.Label("Name")
		self.editname = Gtk.Entry()
		hsizer.pack_start(self.namelabel, expand=False)
		hsizer.add(self.editname)
		vbox.pack_end(hsizer)
		self.vbox.add(vbox)
		self._target = None
		self._name = ''
		self._suggested_name = ''
		self.connect('response', self.on_close)
		self.editname.connect('activate', self.on_editname_activate)
		self.editname.connect('changed', self.on_editname_text)
		eventbus = com.get('neil.core.eventbus')
		eventbus.zzub_midi_control += self.on_player_callback
		self.update()
		self.show_all()
		
	def on_editname_text(self, widget):
		"""
		Handler for name edit field input.
		"""
		self._name = widget.get_text()
		self.update()
		
	def suggest_text(self, text):
		suggested_name = str(text)
		name = self.editname.get_text()
		if (not name) or (name == self._suggested_name):
			self._name = suggested_name
			self._suggested_name = suggested_name
			self.editname.set_text(self._suggested_name)
			self.editname.select_region(0,-1)
		self.update()
		
	def on_editname_activate(self, widget):
		"""
		Called when return is pressed in the edit field.
		"""
		self.update()
		if self.btnok.get_property('sensitive'):
			self.response(Gtk.ResponseType.OK)
		
	def update(self):
		"""
		Decides whether the user can click OK or not. A controller value must
		be recorded and a name must have been entered.
		"""
		if self._target and self._name:
			self.btnok.set_sensitive(True)
		else:
			self.btnok.set_sensitive(False)
		
	def on_player_callback(self, status, ctrl, data):
		"""
		callback for ui events sent by zzub.

		@param status: something to do with midi status?
		@type status: int
		@param controller: midi controller, eg 1 for modwheel, 7 for volume
		@type controller: int
		@param data: midi event data.
		@type data: int
		"""
		cmd = status >> 4
		if cmd == 0xb:
			channel = status & 0xf
			controller = ctrl
			value = data
			self.controllerlabel.set_label(prepstr("%i" % controller))
			self.channellabel.set_label(prepstr("%i" % (channel+1)))
			self.valuelabel.set_label(prepstr("%i" % value))
			self._target = channel,controller
			self.suggest_text("CC #%03i (CH%02i)" % (channel+1, controller))
			self.update()
		
	def on_close(self, widget, response):
		"""
		Called when the dialog is closed.
		"""
		# FIXME should we remove on_player_callback from the eventbus?
		pass
		
def learn_controller(parent):
	dlg = SelectControllerDialog(parent)
	response = dlg.run()
	dlg.destroy()
	if response == Gtk.ResponseType.OK:
		channel,ctrlid = dlg._target
		return dlg._name, channel, ctrlid
	return None

if __name__ == '__main__':
	import testplayer, gobject
	from .testplayer import TestWindow
	window = TestWindow()
	def show_dialog(rootwindow):
		print(learn_controller(rootwindow, rootwindow))
	GObject.timeout_add(100, show_dialog, window)
	Gtk.main()
