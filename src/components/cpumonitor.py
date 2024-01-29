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
Provides dialog class for cpu monitor.
"""

from gi.repository import GObject, Gtk
from neil.utils import prepstr, add_scrollbars
import neil.utils as utils, os, stat
import neil.common as common
from neil.common import MARGIN, MARGIN2, MARGIN3
import neil.com as com

class CPUMonitorDialog(Gtk.Dialog):
    """
    This Dialog shows the CPU monitor, which allows monitoring
    CPU usage and individual plugin CPU consumption.
    """
    
    __neil__ = dict(
        id = 'neil.core.cpumonitor',
        singleton = True,
        categories = [
            'viewdialog',
            'view',
        ]
    )
    
    __view__ = dict(
        label = "CPU Monitor",
        order = 0,
        toggle = True,
    )
        
    def __init__(self):
        """
        Initializer.
        """
        Gtk.Dialog.__init__(self)
        self.connect('delete-event', self.hide_on_delete)
        self.set_size_request(200,300)
        self.set_title("CPU Monitor")
        self.pluginlist = Gtk.ListStore(str, str)
        scrollwin = Gtk.ScrolledWindow()
        scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.pluginlistview = Gtk.TreeView(self.pluginlist)
        self.pluginlistview.set_rules_hint(True)
        self.tvplugin = Gtk.TreeViewColumn("Plugin")
        self.tvplugin.set_resizable(True)
        self.tvload = Gtk.TreeViewColumn("CPU Load")
        self.cellplugin = Gtk.CellRendererText()
        self.cellload = Gtk.CellRendererText()
        self.tvplugin.pack_start(self.cellplugin, expand=False)
        self.tvload.pack_start(self.cellload, expand=False)
        self.tvplugin.add_attribute(self.cellplugin, 'text', 0)
        self.tvload.add_attribute(self.cellload, 'text', 1)
        self.pluginlistview.append_column(self.tvplugin)
        self.pluginlistview.append_column(self.tvload)
        self.pluginlistview.set_search_column(0)
        self.tvplugin.set_sort_column_id(0)
        self.tvload.set_sort_column_id(1)
        self.labeltotal = Gtk.Label("100%")
        self.gaugetotal = Gtk.ProgressBar()
        sizer = Gtk.VBox(False, MARGIN)
        sizer.set_border_width(MARGIN)
        sizer.pack_start(add_scrollbars(self.pluginlistview), expand=False, fill=False, padding=0)
        hsizer = Gtk.HBox(False, MARGIN)
        hsizer.pack_start(self.gaugetotal, expand=False, fill=False, padding=0)
        hsizer.pack_start(self.labeltotal, expand=False, fill=False, padding=0)
        sizer.pack_start(hsizer, expand=False, fill=False, padding=0)
        self.vbox.add(sizer)
        GObject.timeout_add(1000, self.on_timer)

    def on_timer(self):
        """
        Called by timer event. Updates CPU usage statistics.
        """
        player = com.get('neil.core.player')
        driver = com.get('neil.core.driver.audio')
        if self.window and self.window.is_visible():
            cpu = 0.0
            cpu_loads = {}
            cpu = driver.get_cpu_load()
            for mp in player.get_plugin_list():
                cpu_loads[mp.get_name()] = mp.get_last_cpu_load()
            self.gaugetotal.set_fraction(cpu)
            self.labeltotal.set_label("%i%%" % int((cpu*100) + 0.5))
            
            class UpdateNode:
                newvalues = {}
                to_delete = []
            
            def update_node(store, level, item, udata):
                ref = Gtk.TreeRowReference(store, store.get_path(item))
                name = self.pluginlist.get_value(item, 0)
                if name in cpu_loads:
                    relperc = cpu_loads[name] * 100.0
                    un.newvalues[ref] = "%.1f%%" % relperc
                    del cpu_loads[name]
                else:
                    un.to_delete.append(ref)
                
            un = UpdateNode()
            self.pluginlist.foreach(update_node, un)
            for ref in un.to_delete:
                if ref.valid():
                    path = ref.get_path()
                    self.pluginlist.remove(self.pluginlist.get_iter(path))
            for ref,value in list(un.newvalues.items()):
                if ref.valid():
                    path = ref.get_path()
                    self.pluginlist.set_value(self.pluginlist.get_iter(path), 1, value)
                
            for k,v in list(cpu_loads.items()):
                k = prepstr(k)
                relperc = v * 100.0
                self.pluginlist.append([k, "%.1f%%" % relperc])
            self.pluginlistview.columns_autosize()
        return True

__all__ = [
'CPUMonitorDialog',
]

__neil__ = dict(
    classes = [
        CPUMonitorDialog,
    ],
)

