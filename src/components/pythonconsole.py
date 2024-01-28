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
A view that allows browsing available extension interfaces and documentation.

This module can also be executed standalone.
"""

from gi.repository import GObject, Gtk, Pango
GObject.threads_init()
import os
import inspect

import neil.com as com
import neil.utils as utils

import neil.contextlog as contextlog

import fnmatch

MARGIN = 6

VIEW_CLASS = Gtk.TextView
BUFFER_CLASS = Gtk.TextBuffer

import _thread
import time
import code

class PythonConsoleDialog(Gtk.Dialog):
	__neil__ = dict(
		id = 'neil.pythonconsole.dialog',
		singleton = True,
	)
	
	def __init__(self, hide_on_delete=True):
		Gtk.Dialog.__init__(self,
			"Python Console")
		if hide_on_delete:
			self.connect('delete-event', self.hide_on_delete)
		self.resize(600,500)
		vpack = Gtk.VBox()
		hpack = Gtk.HBox()
		self.shell = Gtk.MenuBar()
		toolitem = Gtk.MenuItem("Tools")
		self.toolmenu = Gtk.Menu()
		toolitem.set_submenu(self.toolmenu)
		self.shell.append(toolitem)
		self.locals = {}
		for handler in com.get_from_category('pythonconsole.locals'):
			handler.register_locals(self.locals)
		player = com.get('neil.core.player')
		self.locals.update(dict(
			__name__ = "__console__",
			__doc__ = None,
			com = com,
			embed = self.embed,
			factories = self.list_factories,
			categories = self.list_categories,
			facts = self.list_factories,
			cats = self.list_categories,
			new = com.get,
			gtk = gtk,
			vbox = vpack,
			hbox = hpack,
			tool = self.add_tool,
			plugins = self.list_plugins,
			plugs = self.list_plugins,
			player = player,
			create_plugin = self.create_plugin,
			newplug = self.create_plugin,
		))
		self.compiler = code.InteractiveConsole(self.locals)
		
		buffer = BUFFER_CLASS()
		
		view = VIEW_CLASS(buffer)
		cfg = com.get('neil.core.config')
		# "ProFontWindows 9"
		view.modify_font(Pango.FontDescription(cfg.get_pattern_font('Monospace')))
		view.set_editable(False)
		view.set_wrap_mode(Gtk.WrapMode.WORD)
		self.consoleview = view
		self.buffer = buffer
		self.entry = Gtk.ComboBoxText.new_with_entry()
		self.entry.child.modify_font(Pango.FontDescription(cfg.get_pattern_font('Monospace')))
		renderer = self.entry.get_cells()[0]
		renderer.set_property('font-desc', Pango.FontDescription(cfg.get_pattern_font('Monospace')))
		
		self.entry.child.connect('activate', self.on_entry_activate)
		self.textmark = self.buffer.create_mark(None, self.buffer.get_end_iter(), False)

		scrollwin = Gtk.ScrolledWindow()
		scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		scrollwin.set_shadow_type(Gtk.ShadowType.IN)
		scrollwin.add(self.consoleview)
		
		vpack.pack_start(self.shell, False)
		vpack.pack_start(scrollwin)
		vpack.pack_end(self.entry, False)
		hpack.pack_start(vpack)
		self.vbox.add(hpack)
		
		GObject.timeout_add(50, self.update_output)
		self.log_buffer_pos = 0
		self.entry.grab_focus()
		
		for command in cfg.debug_commands:
			self.add_tool(command, add_to_config=False)
		
	def add_tool(self, cmd, name = None, add_to_config=True):
		if not name:
			name = cmd
		item = Gtk.MenuItem(name)
		item.connect('activate', self.exec_tool, cmd)
		item.show()
		self.toolmenu.append(item)
		if add_to_config:
			config = com.get('neil.core.config')
			config.debug_commands = config.debug_commands + [cmd]
		
	def exec_tool(self, menuitem, cmd):
		self.command(cmd)
		
	def list_categories(self):
		for category in com.categories:
			print(category)
		
	def list_factories(self):
		for factory,item in list(com.factories.items()):
			print((factory,'=',item['classobj']))
			
	def list_plugins(self, pattern='*'):
		uris = []
		player = com.get('neil.core.player')
		for pl in player.get_pluginloader_list():
			uri = pl.get_uri()
			if fnmatch.fnmatch(uri, pattern):
				uris.append(uri)
		return uris
		
	def create_plugin(self, pattern='*'):
		player = com.get('neil.core.player')
		for uri in self.list_plugins(pattern):
			pl = player.get_pluginloader_by_name(uri)
			player.create_plugin(pl)
		
	def embed(self, widget):
		anchor = self.buffer.create_child_anchor(self.buffer.get_end_iter())
		self.consoleview.add_child_at_anchor(widget, anchor)
		widget.show_all()
		print()
		
	def push_text(self, text):
		if self.compiler.push(text):
			self.entry.child.set_text("  ")
			self.entry.child.select_region(99,-1)
		
	def command(self, text):
		print(('>>> ' + text))
		GObject.timeout_add(50, self.push_text, text)
		
	def on_entry_activate(self, widget):
		text = self.entry.child.get_text()
		self.entry.child.set_text("")
		if text.strip() == "":
			text = ""
		self.command(text)
		model = self.entry.get_model()
		it = model.get_iter_first()
		while it:
			if model.get_value(it, 0) == text:
				return
			it = model.iter_next(it)
		self.entry.append_text(text)
		
	def update_output(self):
		while self.log_buffer_pos != len(contextlog.LOG_BUFFER):
			target, filename, lineno, text = contextlog.LOG_BUFFER[self.log_buffer_pos]
			self.buffer.insert(self.buffer.get_end_iter(), text) 
			self.log_buffer_pos += 1
			self.consoleview.scroll_mark_onscreen(self.textmark)
		return True

class PythonConsoleMenuItem:
	__neil__ = dict(
		id = 'neil.pythonconsole.menuitem',
		singleton = True,
		categories = [
			'menuitem.tool'
		],
	)
	
	def __init__(self, menu):
		# create a menu item
		item = Gtk.MenuItem(label="Show _Python Console")
		# connect the menu item to our handler
		item.connect('activate', self.on_menuitem_activate)
		# append the item to the menu
		menu.append(item)
		
	def on_menuitem_activate(self, widget):
		browser = com.get('neil.pythonconsole.dialog')
		browser.show_all()

__neil__ = dict(
	classes = [
		PythonConsoleDialog,
		PythonConsoleMenuItem,
	],
)

if __name__ == '__main__': # extension mode
	import contextlog
	contextlog.init()
	com.load_packages()
	# running standalone
	browser = com.get('neil.pythonconsole.dialog', False)
	browser.connect('destroy', lambda widget: Gtk.main_quit())
	browser.show_all()
	Gtk.main()
