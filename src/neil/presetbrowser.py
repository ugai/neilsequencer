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
Contains all classes and functions needed to render the preset browser.
"""

import sys,os
from gi.repository import GObject, Gtk, cairo, PangoCairo
from .utils import prepstr, filepath, db2linear, linear2db, is_debug, filenameify, \
    get_item_count, question, error, new_listview, add_scrollbars, get_clipboard_text, set_clipboard_text, \
    gettext, new_stock_image_button, diff, file_filter
import config
import zzub
import sys,os
from .preset import PresetCollection, Preset
from . import common
import neil.com as com

class PresetView(Gtk.VBox):
    """
    Rack panel.
    
    Displays controls for individual plugins.
    """
    def __init__(self, rootwindow, plugin, parent):
        """
        Initialization.
        """
        Gtk.VBox.__init__(self)
        self.set_size_request(150, 400)
        self.rootwindow = rootwindow
        self.plugin = plugin
        self.pluginloader = plugin.get_pluginloader()
        self.panels = {}
        scrollwindow = Gtk.ScrolledWindow()
        scrollwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.presetlist, self.presetstore, columns = new_listview([('Name', str),])
        self.presetlist.get_selection().set_mode(Gtk.SELECTION_MULTIPLE)
        self.update_presets()
        scrollwindow.add_with_viewport(self.presetlist)
        self.scrollwindow = scrollwindow        
        self.pack_start(self.scrollwindow)        

        self.presetlist.connect("row-activated", self.on_row_activate)
        
        buttonbox = Gtk.HBox()
        buttonbox.set_size_request(-1, 50)
        button_import = Gtk.Button('Import')
        button_export = Gtk.Button('Export')        
        button_delete = Gtk.Button('Delete')                
        buttonbox.pack_start(button_import, padding=5)        
        buttonbox.pack_start(button_export, padding=5)        
        buttonbox.pack_start(button_delete, padding=5)        
        self.pack_start(buttonbox, expand=False, padding=5)
        
        button_import.connect('clicked', self.on_import)
        button_export.connect('clicked', self.on_export)
        button_delete.connect('clicked', self.on_delete)        
        self.export_dlg = Gtk.FileChooserDialog(title="Export", parent=parent, action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        self.import_dlg = Gtk.FileChooserDialog(title="Import", parent=parent, action=Gtk.FileChooserAction.OPEN,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        filter = file_filter("Preset files (*.prs)", "*.prs")
        self.export_dlg.add_filter(filter)
        self.import_dlg.add_filter(filter)
        self.export_dlg.set_do_overwrite_confirmation(True)
        
    def update_presets(self):
        self.presets = config.get_config().get_plugin_presets(self.pluginloader)
        self.presetstore.clear()
        for preset in self.presets.presets:
            self.presetstore.append([prepstr(preset.name)])

    def on_delete(self, widget):                
        model, rows = self.presetlist.get_selection().get_selected_rows()
        if rows:
            if len(rows) > 1:
                if question(self, '<b><big>Really delete %s presets?</big></b>' % len(rows),False) != Gtk.ResponseType.YES:
                    return
            elif question(self, '<b><big>Really delete preset?</big></b>',False) != Gtk.ResponseType.YES:
                return
            selected = [self.presets.presets[row[0]] for row in rows]
            for preset in selected:
                self.presets.presets.remove(preset)            
            config.get_config().set_plugin_presets(self.pluginloader, self.presets)
            self.update_presets()
        
    def on_export(self, widget):
        response = self.export_dlg.run()        
        self.export_dlg.hide()
        if response == Gtk.ResponseType.OK:
            model, rows = self.presetlist.get_selection().get_selected_rows()    
            filename = self.export_dlg.get_filename()    
            #~ if not os.path.splitext(filename)[1]:
                #~ filename += '.prs'
            new_presets = PresetCollection()
            selected = [self.presets.presets[row[0]] for row in rows]
            for preset in selected:        
                new_presets.presets.append(preset)
            new_presets.save(filename)
        
    def on_import(self, widget):        
        response = self.import_dlg.run()
        self.import_dlg.hide()        
        if response == Gtk.ResponseType.OK:
            try:
                new_presets = PresetCollection(self.import_dlg.get_filename())                
                # Test them first
                for preset in new_presets.presets:
                    try:
                        preset.apply(self.plugin, dryrun=True)
                    except AssertionError:
                        txt = "This preset file seems intended for a different plugin."
                        print(txt)
                        error(self, txt)
                        return
                # If they're all ok, add them
                for preset in new_presets.presets:
                    self.presets.presets.append(preset)
                self.presets.sort()                
                config.get_config().set_plugin_presets(self.pluginloader, self.presets)                
                self.update_presets()
            except:
                import traceback
                print(traceback.format_exc())            
        
    def on_row_activate(self, treeview, path, view_column):
        preset = self.presets.presets[path[0]]
        preset.apply(self.plugin)
        player = com.get('neil.core.player')
        player.history_commit("change preset")


    def get_title(self):
        name = prepstr(self.plugin.get_name())        
        classname = prepstr(self.pluginloader.get_name())
        return "%s - %s" % (name,classname)        
        

if __name__ == '__main__':
    from . import testplayer, utils
    player = testplayer.get_player()
    player.load_ccm(utils.filepath('test.ccm'))
    window = testplayer.TestWindow()
    rack = PresetView(window,  player.get_plugin(1), window)
    window.add(rack)
    window.show_all()
    
    Gtk.main()
