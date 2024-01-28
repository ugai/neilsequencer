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
Contains all classes and functions needed to render the rack view.
"""

from gi.repository import GObject, Gtk, cairo, PangoCairo
from neil.utils import prepstr, filepath, db2linear, linear2db, is_debug, filenameify, \
	get_item_count, question, error, new_listview, add_scrollbars, get_clipboard_text, set_clipboard_text, \
	gettext, new_stock_image_button, diff, show_machine_manual
import zzub
import sys,os
import fnmatch
import ctypes
import time
import queue
import neil.common as common
import neil.preset as preset_module
from neil.common import MARGIN, MARGIN2, MARGIN3, MARGIN0
import pickle
import config
import neil.com as com

class ParameterView(Gtk.VBox):
    """
    Displays parameter sliders for a plugin in a new Dialog.
    """

    UNBIND_ALL = 'unbind-all'
    CONTROLLER = 'controller'

    DROP_TARGET_CTRL_SLIDER = 0

    DROP_TARGETS = [
	    ('application/x-controller-slider-drop', Gtk.TargetFlags.SAME_APP, DROP_TARGET_CTRL_SLIDER),
    ]

    __neil__ = dict(
	    id = 'neil.core.parameterview',
	    singleton = False,
	    categories = [
	    ]
    )

    def __init__(self, plugin):
        """
        Initializer.

        @param plugin: The plugin object for which to display parameters.
        @type plugin: zzub.Plugin
        """
        Gtk.VBox.__init__(self)
        self.set_flags(Gtk.CAN_FOCUS)
        self.plugin = plugin
        self.tooltips=Gtk.Tooltips()
        name = prepstr(self.plugin.get_name())
        pl = self.plugin.get_pluginloader()
        classname = prepstr(pl.get_name())
        title = "%s - %s" % (name,classname)
        self._title = title

        self.presetbox = Gtk.ComboBoxText.new_with_entry()
        self.presetbox.set_size_request(100,-1)
        self.presetbox.set_wrap_width(4)
        self.btnadd = new_stock_image_button(Gtk.STOCK_ADD)
        self.tooltips.set_tip(self.btnadd, "Write Values to Preset")
        self.btnremove = new_stock_image_button(Gtk.STOCK_REMOVE)
        self.tooltips.set_tip(self.btnremove, "Delete Preset")
        self.btncopy = new_stock_image_button(Gtk.STOCK_COPY)
        self.tooltips.set_tip(self.btncopy, "Copy Values to Clipboard (to Paste in Pattern)")
        self.btnrandom = Gtk.Button("_Random")
        self.tooltips.set_tip(self.btnrandom, "Randomise Values")
        self.btnhelp = new_stock_image_button(Gtk.STOCK_HELP)
        self.tooltips.set_tip(self.btnhelp, "Help")
        menugroup = Gtk.HBox(False, MARGIN)
        menugroup.pack_start(self.presetbox)
        menugroup.pack_start(self.btnadd, expand=False)
        menugroup.pack_start(self.btnremove, expand=False)
        menugroup.pack_start(self.btncopy, expand=False)
        menugroup.pack_start(self.btnrandom, expand=False)
        menugroup.pack_start(self.btnhelp, expand=False)
        toplevelgroup = Gtk.VBox(False, MARGIN)
        toplevelgroup.set_border_width(MARGIN)
        toplevelgroup.pack_start(menugroup, expand=False)

        scrollwindow = Gtk.ScrolledWindow()
        scrollwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.pluginloader = pl

        self.update_presets()

        rowgroup = Gtk.VBox()
        rowgroup.set_border_width(MARGIN)
        self.id2pid = {}
        self.pid2ctrls = {}

        self.create_sliders(rowgroup)

        self.btnadd.connect('clicked', self.on_button_add)
        self.btnremove.connect('clicked', self.on_button_remove)
        self.btncopy.connect('clicked', self.on_button_copy)
        self.btnrandom.connect('clicked', self.on_button_random)
        self.btnhelp.connect('clicked', self.on_button_help)
        self.connect('destroy', self.on_destroy)
        routeview = com.get('neil.core.routerpanel').view
        self.connect('key-press-event', routeview.on_key_jazz, self.plugin)		
        self.connect('key-release-event', routeview.on_key_jazz_release, self.plugin)
        self.connect('button-press-event', self.on_left_down)

        self.presetbox.set_active(0)
        self.presetbox.connect('changed', self.on_select_preset)

        scrollwindow.add_with_viewport(rowgroup)
        self.scrollwindow = scrollwindow
        self.rowgroup = rowgroup
        toplevelgroup.add(scrollwindow)

        self.add(toplevelgroup)		
        eventbus = com.get('neil.core.eventbus')
        eventbus.zzub_parameter_changed += self.on_zzub_parameter_changed
        self.update_preset_buttons()

    def on_zzub_parameter_changed(self, plugin, group, track, param, value):
        """
        parameter window callback for ui events sent by zzub.

        @param player: player instance.
        @type player: zzub.Player
        @param plugin: plugin instance
        @type plugin: zzub.Plugin
        @param data: event data.
        @type data: zzub_event_data_t
        """
        # exit if this is called and dialog is hidden
        if not self.flags() & Gtk.VISIBLE:
            return

        if plugin == self.plugin:
            g,t,i,v = group, track, param, value
            p = self.pluginloader.get_parameter(g,i)
            # Try to get the parameter. If we can't, it might be an incoming amp/pan
            # parameter (g == 0). Either way we can update the rack.
            if (p and (p.get_flags() & zzub.zzub_parameter_flag_state)) or (not p and g == 0):
                nl, s, vl = self.pid2ctrls[(g, t, i)]
                v = self.plugin.get_parameter_value(g,t,i)
                s.set_value(v)
                self.update_valuelabel(g, t, i)

    def create_sliders(self, rowgroup):
        plugin = self.plugin
        pl = self.pluginloader
        snamegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        sslidergroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        svaluegroup = Gtk.SizeGroup(Gtk.SizeGroupMode.HORIZONTAL)
        def add_controller(g, t, i):
            p = plugin.get_parameter(g, t, i)
            name = "CC-%s" % prepstr(p.get_name())
            namelabel = Gtk.Label()
            namelabel._default_name = name
            button = Gtk.Button('Drag to connect')
            button.drag_source_set(Gdk.BUTTON1_MASK | Gdk.BUTTON3_MASK,
                self.DROP_TARGETS, Gdk.ACTION_COPY)
            button.connect('drag-data-get', self.on_drag_data_get, (g, t, i))
            button.connect('drag-data-delete', self.on_drag_data_delete, 
                            (g, t, i))
            button.connect('drag-end', self.on_drag_end, (g, t, i))
            snamegroup.add_widget(namelabel)
            namelabel.set_alignment(0, 0.5)
            valuelabel = Gtk.Label("")
            valuelabel.set_alignment(0, 0)
            valuelabel.set_size_request(80, -1)
            slidergroup = Gtk.HBox(False, MARGIN)
            slidergroup.pack_start(namelabel, expand=False)	
            slidergroup.add(button)
            slidergroup.pack_end(valuelabel, expand=False)
            sslidergroup.add_widget(button)
            svaluegroup.add_widget(valuelabel)
            rowgroup.pack_start(slidergroup, expand=False)
            self.pid2ctrls[(g, t, i)] = [namelabel, button, None]
            button.connect('button-press-event', self.on_context_menu, (g,t,i))
            namelabel.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
            namelabel.connect('button-press-event', self.on_context_menu, (g,t,i))
            self.update_namelabel(g, t, i)

        def add_nonstate_param(g, t, i):
            p = plugin.get_parameter(g,t,i)
            if g == 2:
                name = "%i-%s" % (t,prepstr(p.get_name()))
            else:
                name = prepstr(p.get_name())
            namelabel = Gtk.Label()
            namelabel._default_name = name
            button = Gtk.Button('Drop here to connect')
            button.drag_dest_set(Gtk.DEST_DEFAULT_ALL, self.DROP_TARGETS,
                Gdk.ACTION_COPY)
            button.connect('drag-data-received', self.on_drag_data_received, (g,t,i))
            button.connect('drag-drop', self.on_drag_drop, (g,t,i))
            snamegroup.add_widget(namelabel)
            namelabel.set_alignment(0, 0.5)
            valuelabel = Gtk.Label("")
            valuelabel.set_alignment(0, 0)
            valuelabel.set_size_request(80, -1)
            slidergroup = Gtk.HBox(False, MARGIN)
            slidergroup.pack_start(namelabel, expand=False)	
            slidergroup.add(button)
            slidergroup.pack_end(valuelabel, expand=False)
            sslidergroup.add_widget(button)
            svaluegroup.add_widget(valuelabel)
            rowgroup.pack_start(slidergroup, expand=False)
            self.pid2ctrls[(g,t,i)] = [namelabel,button,None]
            button.connect('button-press-event', self.on_context_menu, (g,t,i))
            namelabel.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
            namelabel.connect('button-press-event', self.on_context_menu, (g,t,i))
            self.update_namelabel(g,t,i)

        def add_slider(g, t, i):
            p = plugin.get_parameter(g, t, i)
            if not (p.get_flags() & zzub.zzub_parameter_flag_state):
                return add_nonstate_param(g, t, i)
            if g == 0:
                try:
                    in_plugin = self.plugin.get_input_connection_plugin(t)
                    in_machine_name = in_plugin.get_name()
                except:
                    in_machine_name = ""
                volpanstr = ["Vol", "Pan"][i]
                name = "%s-%i (%s)" % (volpanstr, t, prepstr(in_machine_name))
            elif g == 2:
                name = "%i-%s" % (t, prepstr(p.get_name()))
            else:
                name = prepstr(p.get_name())
            namelabel = Gtk.Label()
            namelabel._default_name = name
            slider = Gtk.HScale()
                #slider.set_tooltip_markup(p.get_description())
            slider.set_property('draw-value', False)
            slider.set_range(p.get_value_min(),p.get_value_max())
            # set increment size for left and right arrow and mouse clicks
            increment = (p.get_value_max() - p.get_value_min()) / 10
            slider.set_increments(1, increment)
            v = plugin.get_parameter_value(g, t, i)
            slider.set_tooltip_markup("<b>Description</b>: %s" % p.get_description())
            slider.set_value(v)
            slider.drag_dest_set(Gtk.DEST_DEFAULT_ALL, self.DROP_TARGETS,
                Gdk.ACTION_COPY)
            slider.connect('drag-data-received', self.on_drag_data_received, (g, t, i))
            slider.connect('drag-drop', self.on_drag_drop, (g, t, i))
            valuelabel = Gtk.Label("")
            valuelabel.set_alignment(0, 0)
            valuelabel.set_size_request(80, -1)

            snamegroup.add_widget(namelabel)
            namelabel.set_alignment(0, 0)
            sslidergroup.add_widget(slider)
            svaluegroup.add_widget(valuelabel)

            slidergroup = Gtk.HBox(False, MARGIN)
            slidergroup.pack_start(namelabel, expand=False)	
            slidergroup.add(slider)	
            slidergroup.pack_end(valuelabel, expand=False)	
            rowgroup.pack_start(slidergroup, expand=False)
            self.pid2ctrls[(g, t, i)] = [namelabel, slider, valuelabel]
            slider.connect('button-press-event', self.on_context_menu, (g, t, i))
            namelabel.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
            namelabel.connect('button-press-event', self.on_context_menu, (g, t, i))
            valuelabel.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
            valuelabel.connect('button-press-event', self.on_context_menu, (g, t, i))
            slider.connect('scroll-event', self.on_mousewheel, (g, t, i))
            slider.connect('button-press-event', self.on_button_press, (g, t, i))
            slider.connect('change-value', self.on_scroll_changed, (g, t, i))
            slider.connect('key-press-event', self.on_key_down, (g, t, i))
            self.update_valuelabel(g, t, i)
            self.update_namelabel(g, t, i)

        # input connections
        for t in range(plugin.get_input_connection_count()):
            connectiontype = plugin.get_input_connection_type(t)
            if connectiontype == zzub.zzub_connection_type_audio:
                for i in range(2): # volume and pan
                    add_slider(0, t, i)
        # globals
        for i in range(pl.get_parameter_count(1)):
            add_slider(1, 0, i)
        # tracks
        for t in range(plugin.get_track_count()):
            for i in range(pl.get_parameter_count(2)):
                add_slider(2, t, i)
        # controllers
        for i in range(pl.get_parameter_count(3)):
            add_controller(3, 0, i)

    def on_left_down(self, widget, event, data=None):
        self.grab_focus()

    def get_best_size(self):
        rc = self.get_allocation()
        cdx,cdy,cdw,cdh = rc.x, rc.y, rc.width, rc.height
        rc = self.rowgroup.get_allocation()
        svx, svy = rc.width, rc.height
        rc = self.scrollwindow.get_allocation()
        swx,swy = rc.width, rc.height
        ofsy = cdh - swy # size without scrollwindow
        return max(swx,400), min((svy+20+ofsy),(3*Gdk.screen_height())/4)

    def get_title(self):
	    return self._title

    def on_drag_data_get(self, btn, context, selection_data, info, time, xxx_todo_changeme):
        (g,t,i) = xxx_todo_changeme
        if info == self.DROP_TARGET_CTRL_SLIDER:
            text = pickle.dumps((self.plugin.get_id(), g, t, i))
            selection_data.set(selection_data.target, 8, text)

    def on_drag_data_delete(self, btn, context, data, xxx_todo_changeme1):
        (g,t,i) = xxx_todo_changeme1
        pass

    def on_drag_drop(self, w, context, x, y, time, xxx_todo_changeme2):
        (g,t,i) = xxx_todo_changeme2
        return True

    def on_drag_end(self, w, context, xxx_todo_changeme3):
        (g,t,i) = xxx_todo_changeme3
        self.update_namelabel(g, t, i)

    def find_event_connection(self, source):
        for index in range(self.plugin.get_input_connection_count()):
            conn = self.plugin.get_input_connection_plugin(index)
            connectiontype = self.plugin.get_input_connection_type(index)
            if connectiontype == zzub.zzub_connection_type_event:
                if conn == source:
                    return conn
        return None

    def connect_controller(self, source,sg,st,si,tg,tt,ti):
        conn = self.find_event_connection(source)
        if not conn:
            # no connection, so we make a new one
            self.plugin.add_input(source, zzub.zzub_connection_type_event)
            conn = self.find_event_connection(source)
            if not conn: # we can't make one
                error(self, "<big><b>Cannot connect parameters.</b></big>")
                return
        self.plugin.add_event_connection_binding(source, si,tg,tt,ti)
        self.update_namelabel(tg,tt,ti)

    def on_drag_data_received(self, w, context, x, y, data, info, time, xxx_todo_changeme4):
        (g,t,i) = xxx_todo_changeme4
        player = com.get('neil.core.player')
        try:
            if data and data.format == 8:
                plugin_id, sg, st, si = pickle.loads(data.data)
                for plugin in player.get_plugin_list():
                    if plugin.get_id() == plugin_id:
                        self.connect_controller(plugin, sg, st, si, g, t, i)
                        player.history_commit("add event connection")
                        break
                context.finish(True, False, time)
                return
        except:
            import traceback
            traceback.print_exc()
        context.finish(False, False, time)

    def on_unbind(self, widget, xxx_todo_changeme5):
        """
        Unbinds all midi controllers from the selected parameter.
        """
        (g,t,i) = xxx_todo_changeme5
        player = com.get('neil.core.player')
        player.remove_midimapping(self.plugin, g, t, i)
        self.update_namelabel(g,t,i)
        player.history_commit("remove MIDI mapping")

    def on_unbind_event_connection_binding(self, widget, xxx_todo_changeme6):
        """
        Unbinds all event connection bindings from the selected parameter.
        """
        (g,t,i) = xxx_todo_changeme6
        conns = []
        while True:
            result = self.get_event_connection_bindings(g,t,i)
            if not result:
                break
            conn,c = result[0]
            cv = conn.get_event_connection()
            cv.remove_binding(c)
            if not conn in conns:
                conns.append(conn)
        # remove all connections without any binding
        for conn in conns:
            if conn.get_event_connection().get_binding_count() == 0:
                conn.get_output().delete_input(conn.get_input())
        self.update_namelabel(g,t,i)

    def on_learn_controller(self, widget, xxx_todo_changeme7):
        """
        Handles the learn entry from the context menu. Associates
        a controller with a plugin parameter.
        """
        (g, t, i) = xxx_todo_changeme7
        import neil.controller as controller
        player = com.get('neil.core.player')
        res = controller.learn_controller(self)
        if res:
            name, channel, ctrlid = res
            player.add_midimapping(self.plugin, g, t, i, channel, ctrlid)
            player.history_commit("add MIDI mapping")
        self.update_namelabel(g, t, i)

    def on_bind_controller(self, widget, xxx_todo_changeme8, xxx_todo_changeme9):
        """
        Handles clicks on controller names in the context menu. Associates
        a controller with a plugin parameter.
        """
        (g, t, i) = xxx_todo_changeme8
        (name, channel, ctrlid) = xxx_todo_changeme9
        player = com.get('neil.core.player')
        # FIXME: commented-out for now, because midi controllers crash neil
        # after closing and reopening a rack.
        player.add_midimapping(self.plugin, g, t, i, channel, ctrlid)
        player.history_commit("add MIDI mapping")
        self.update_namelabel(g, t, i)

    def get_event_connection_bindings(self, g,t,i):
        # 0.3: DEAD
        # no event connection implementation right now
        return []
        result = []
        if g == 3:
            # we are the source
            for conn in self.plugin.get_output_connection_list():
                if conn.get_type() == zzub.zzub_connection_type_event:
                    cv = conn.get_event_connection()
                    for c in range(cv.get_binding_count()):
                        binding = cv.get_binding(c)
                        if binding.get_controller() == i:
                            result.append((conn,c))
        else:
            # we are the target
            for conn in self.plugin.get_input_connection_list():
                if conn.get_type() == zzub.zzub_connection_type_event:
                    cv = conn.get_event_connection()
                    for c in range(cv.get_binding_count()):
                        binding = cv.get_binding(c)
                    if (binding.get_group() == g) and (binding.get_track() == t) and (binding.get_column() == i):
                        result.append((conn,c))
        return result

    # this fails to add italics to event-connected parameters
    # because get_event_connection_bindings() is broken, for now.
    def update_namelabel(self, g, t, i):
        player = com.get('neil.core.player')
        nl, s, vl = self.pid2ctrls[(g, t, i)]
        markup = "<b>%s</b>" % nl._default_name
        if self.get_event_connection_bindings(g, t, i):
            markup = "<i>%s</i>" % markup
        for mm in player.get_midimapping_list():
            mp, mg, mt, mi = mm.get_plugin(), mm.get_group(), mm.get_track(), mm.get_column()
            if (player.get_plugin_by_id(mp) == self.plugin) and ((mg, mt, mi) == (g, t, i)):
                markup = "<u>%s</u> [%d]" % (markup, mm.get_controller())
                break
        nl.set_markup(markup)

    def on_context_menu(self, widget, event, xxx_todo_changeme10):
        """
        Event handler for requests to show the context menu.

        @param event: event.
        @type event: wx.Event
        """
        (g,t,i) = xxx_todo_changeme10
        player = com.get('neil.core.player')
        if event.button == 1:
            nl,s,vl = self.pid2ctrls[(g,t,i)]
            s.grab_focus()
        elif event.button == 3:
            nl,s,vl = self.pid2ctrls[(g,t,i)]
            menu = Gtk.Menu()
            def make_submenu_item(submenu, name):
                item = Gtk.MenuItem(label=name)
                item.set_submenu(submenu)
                return item
            def make_menu_item(label, desc, func, *args):
                item = Gtk.MenuItem(label=label)
                if func:
                    item.connect('activate', func, *args)
                return item
            def cmp_nocase(a,b):
                return cmp(a[0].lower(),b[0].lower())
            evbinds = self.get_event_connection_bindings(g,t,i)
            if g == 3:
                for conn,c in evbinds:
                    cv = conn.get_event_connection()
                    binding = cv.get_binding(c)
                    paramname = conn.get_output().get_pluginloader().get_parameter(binding.get_group(),binding.get_column()).get_name()
                    if binding.get_group() == 2:
                        paramname = "%i-%s" % (binding.get_track(), paramname)
                    label = "Bound to %s: %s" % (conn.get_output().get_name(), paramname)
                    item = Gtk.MenuItem(label=label)
                    item.set_sensitive(False)
                    menu.append(item)
                if evbinds:
                    menu.append(Gtk.SeparatorMenuItem())
                    menu.append(make_menu_item("_Unbind Controller from Targets", "", self.on_unbind_event_connection_binding, (g,t,i)))
                else:
                    return False
            else:
                index = 0
                submenu = Gtk.Menu()
                for name,channel,ctrlid in sorted(config.get_config().get_midi_controllers(), cmp_nocase):
                    submenu.append(make_menu_item(prepstr(name), "", self.on_bind_controller, (g,t,i), (name,channel,ctrlid)))
                    index += 1
                controllers = 0
                for mm in player.get_midimapping_list():
                    mp,mg,mt,mi = mm.get_plugin(), mm.get_group(), mm.get_track(), mm.get_column()
                    if (player.get_plugin_by_id(mp) == self.plugin) and ((mg,mt,mi) == (g,t,i)):
                        label = "Bound to CC #%03i (CH%02i)" % (mm.get_controller(), mm.get_channel()+1)
                        item = Gtk.MenuItem(label=label)
                        item.set_sensitive(False)
                        menu.append(item)
                        controllers +=1
                if controllers:
                    menu.append(Gtk.SeparatorMenuItem())
                if index:
                    menu.append(make_submenu_item(submenu, "_Bind to MIDI Controller"))
                menu.append(make_menu_item("_Learn MIDI Controller", "", self.on_learn_controller, (g,t,i)))
                if controllers:
                    menu.append(Gtk.SeparatorMenuItem())
                    menu.append(make_menu_item("_Unbind Parameter from MIDI", "", self.on_unbind, (g,t,i)))
                if evbinds:
                    menu.append(Gtk.SeparatorMenuItem())
                    for conn,c in evbinds:
                        cv = conn.get_event_connection()
                        binding = cv.get_binding(c)
                        paramname = conn.get_input().get_pluginloader().get_parameter(3,binding.get_controller()).get_name()
                        label = "Bound to %s: %s" % (conn.get_input().get_name(), paramname)
                        item = Gtk.MenuItem(label=label)
                        item.set_sensitive(False)
                        menu.append(item)
                    menu.append(Gtk.SeparatorMenuItem())
                    menu.append(make_menu_item("_Unbind Parameter from Controller", "", self.on_unbind_event_connection_binding, (g, t, i)))
            menu.show_all()
            menu.attach_to_widget(self, None)
            menu.popup(None, None, None, event.button, event.time)
            return True

    def update_presets(self):
        """
        Updates the preset box.
        """
        config = com.get('neil.core.config')
        self.presets = config.get_plugin_presets(self.pluginloader)
        s = self.presetbox.child.get_text()
        self.presetbox.get_model().clear()
        self.presetbox.append_text('<default>')
        for preset in self.presets.presets:
            self.presetbox.append_text(prepstr(preset.name))
        self.presetbox.child.set_text(s)

    def apply_preset(self, preset=None):
        if not preset:
            for g in range(1,3):
                for t in range(self.plugin.get_group_track_count(g)):
                    for i in range(self.pluginloader.get_parameter_count(g)):
                        p = self.pluginloader.get_parameter(g,i)
                        if p.get_flags() & zzub.zzub_parameter_flag_state:
                            self.plugin.set_parameter_value(g,t,i,p.get_value_default(),0)
        else:
            preset.apply(self.plugin)
        player = com.get('neil.core.player')
        player.history_commit("change preset")
        #self.update_all_sliders()

    def on_button_add(self, widget):
        """
        Handler for the Add preset button
        """
        config = com.get('neil.core.config')
        name = self.presetbox.child.get_text()
        presets = [preset for preset in self.presets.presets if prepstr(preset.name) == name]
        if presets:
            preset = presets[0]
        else:
            preset = preset_module.Preset()
            self.presets.presets.append(preset)
        preset.name = name
        preset.comment = ''
        preset.pickup(self.plugin)
        self.presets.sort()
        config.set_plugin_presets(self.pluginloader, self.presets)
        self.update_presets()
        self.update_preset_buttons()

    def on_button_remove(self, widget):
        """
        Handler for the Remove preset button
        """
        config = com.get('neil.core.config')
        name = self.presetbox.child.get_text()
        presets = [preset for preset in self.presets.presets if prepstr(preset.name) == name]
        if presets:
            self.presets.presets.remove(presets[0])
        config.set_plugin_presets(self.pluginloader, self.presets)
        self.update_presets()
        self.update_preset_buttons()

    def update_preset_buttons(self):
        """
        Update presets.
        """
        if self.presetbox.child.get_text() == "<default>":
            self.btnadd.set_sensitive(False)
            self.btnremove.set_sensitive(False)
        elif [preset for preset in self.presets.presets if prepstr(preset.name) == self.presetbox.child.get_text()]:
            self.btnadd.set_sensitive(True)
            self.btnremove.set_sensitive(True)
        else:
            self.btnadd.set_sensitive(True)
            self.btnremove.set_sensitive(True)

    def on_select_preset(self, widget):
        """
        Handler for changes of the choice box. Changes the current parameters
        according to preset.

        @param event: Command event.
        @type event: wx.CommandEvent
        """
        if widget.get_active() == -1:
            pass
        else:
            sel = max(self.presetbox.get_active() - 1,-1)
            if sel == -1:
                self.apply_preset(None)
            else:
                self.apply_preset(self.presets.presets[sel])
        self.update_preset_buttons()

    def update_all_sliders(self):
        """
        Updates all sliders. Should only be called when most sliders
        have been changed at once, e.g. after a preset change.
        """
        for g in range(1,3):
            if g == 1:
                trackcount = 1
            else:
                trackcount = self.plugin.get_track_count()
            for t in range(trackcount):
                for i in range(self.pluginloader.get_parameter_count(g)):
                    p = self.pluginloader.get_parameter(g,i)
                    if p.get_flags() & zzub.zzub_parameter_flag_state:
                        nl, s, vl = self.pid2ctrls[(g,t,i)]
                        v = self.plugin.get_parameter_value(g,t,i)
                        s.set_value(v)
                        self.update_valuelabel(g, t, i)

    def on_button_edit(self, event):
        """
        Handler for clicks on the 'Edit' button. Opens the
        preset dialog.
        """
        dlg = PresetDialog(self.plugin, self)
        dlg.run()
        dlg.destroy()
        self.update_presets()

    def on_button_copy(self, event):
        """
        Handler for clicks on the 'Copy' button. Constructs a paste buffer
        which can be used for pasting in the pattern editor.

        @param event: Command event.
        @type event: wx.CommandEvent
        """
        import patterns
        CLIPBOARD_MAGIC = patterns.PatternView.CLIPBOARD_MAGIC
        data = CLIPBOARD_MAGIC
        data += "%01x" % patterns.SEL_ALL
        for g in range(1,3):
            for t in range(self.plugin.get_group_track_count(g)):
                for i in range(self.pluginloader.get_parameter_count(g)):
                    p = self.pluginloader.get_parameter(g,i)
                    if p.get_flags() & zzub.zzub_parameter_flag_state:
                        v = self.plugin.get_parameter_value(g,t,i)
                        data += "%04x%01x%02x%02x%04x" % (0,g,t,i,v)
        set_clipboard_text(data)

    def on_button_random(self, event):
        """
        Handler for clicks on the 'Random' button.

        @param event: Command event.
        @type event: wx.CommandEvent
        """
        import random
        for g in range(1,3):
            for t in range(self.plugin.get_group_track_count(g)):
                for i in range(self.pluginloader.get_parameter_count(g)):
                    p = self.pluginloader.get_parameter(g,i)
                    if p.get_flags() & zzub.zzub_parameter_flag_state:
                        nl,s,vl = self.pid2ctrls[(g,t,i)]
                        v = random.randint(p.get_value_min(), p.get_value_max())
                        self.plugin.set_parameter_value(g,t,i,v,0)
                        s.set_value(v)
                        self.update_valuelabel(g,t,i)
        player = com.get('neil.core.player')
        player.history_commit("randomize parameters")

    def on_button_help(self, event):
        """
        Handler for clicks on the 'Help' button.

        @param event: Command event.
        @type event: wx.CommandEvent
        """
        name = filenameify(self.pluginloader.get_name())
        if not show_machine_manual(name):
            info=Gtk.MessageDialog(self.get_toplevel(),flags=0, type=Gtk.MESSAGE_INFO, buttons=Gtk.BUTTONS_OK, message_format="Sorry, there's no help for this plugin yet")
            info.run()
            info.destroy()

    def on_key_down(self, widget, event, xxx_todo_changeme11):
        """
        Callback that responds to key stroke.
        """		
        (g,t,i) = xxx_todo_changeme11
        kv = event.keyval
        if (kv >= ord('0')) and (kv <= ord('9')):
            p = self.pluginloader.get_parameter(g,i)
            minv = p.get_value_min()
            maxv = p.get_value_max()
            data_entry = DataEntry((minv,maxv,chr(kv)), self)
            x,y,state = self.window.get_toplevel().get_pointer()
            px,py = self.get_toplevel().get_position()
            data_entry.move(px+x, py+y)
            if data_entry.run() == Gtk.ResponseType.OK:
                try:
                    value = int(data_entry.edit.get_text())
                    nl,s,vl = self.pid2ctrls[(g,t,i)]
                    s.set_value(value)
                    self.plugin.set_parameter_value(g,t,i,int(s.get_value()),0)
                    self.update_valuelabel(g,t,i)
                    player = com.get('neil.core.player')
                    player.history_commit("change plugin parameter")
                except:
                    import traceback
                    traceback.print_exc()
            data_entry.destroy()
            return True
        return False

    def on_destroy(self, event):
        """
        Handles destroy events.
        """
        # player = com.get('neil.core.player')
        # print player.get_midimapping_count()
        # for i in range(player.get_midimapping_count()):
        #     m =  player.get_midimapping(i)
        #     plugin = player.get_plugin_by_id(m.get_plugin())
        #     player.remove_midimapping(plugin, m.get_group(), m.get_track(), m.get_column())
        #     player.history_commit("remove MIDI mapping")	

    def on_button_press(self, widget, event, xxx_todo_changeme12):
        """
        Buttons press on slider
        Used to reset value to default on double click
        """		
        (g,t,i) = xxx_todo_changeme12
        if event.type == Gdk._2BUTTON_PRESS:
            p = self.plugin.get_parameter(g,t,i)
            v = p.get_value_default()
            self.plugin.set_parameter_value(g,t,i,v,1)
            v = self.plugin.get_parameter_value(g,t,i)
            nl,s,vl = self.pid2ctrls[(g,t,i)]
            s.set_value(v)
            self.update_valuelabel(g,t,i)
            player = com.get('neil.core.player')
            player.history_commit("reset plugin parameter")
            # s.emit_stop_by_name('button-press-event')


    def on_mousewheel(self, widget, event, xxx_todo_changeme13):
        """
        Sent when the mousewheel is used on a slider.

        @param event: A mouse event.
        @type event: wx.MouseEvent
        """
        (g,t,i) = xxx_todo_changeme13
        nl,s,vl = self.pid2ctrls[(g,t,i)]
        v = self.plugin.get_parameter_value(g,t,i)
        p = self.plugin.get_parameter(g,t,i)
        minv, maxv = p.get_value_min(), p.get_value_max()
        if event.direction == Gdk.SCROLL_UP:
            v += 1
        elif event.direction == Gdk.SCROLL_DOWN:
            v -= 1
        # apply value range constraint
        v = min(maxv, max(v, minv)) 		
        self.plugin.set_parameter_value(g,t,i,v,1)
        v = self.plugin.get_parameter_value(g,t,i)
        s.set_value(v)
        self.update_valuelabel(g,t,i)
        player = com.get('neil.core.player')
        player.history_commit("change plugin parameter")

    def update_valuelabel(self, g, t, i):
        """
        Updates the right label for a parameter slider.

        @param g: The group this parameter belongs to.
        @type g: int
        @param t: The track of the group this parameter belongs to.
        @type t: int
        @param i: The parameter index within the track.
        @type i: int
        """
        nl, s, vl = self.pid2ctrls[(g, t, i)]
        v = self.plugin.get_parameter_value(g,t,i)
        text = prepstr(self.plugin.describe_value(g, i, v))
        if not text:
            text = "%i" % v
        vl.set_label(text)

    def on_scroll_changed(self, widget, scroll, value, xxx_todo_changeme14):
        """
        Event handler for changes in slider movements.

        @param event: A scroll event.
        @type event: wx.ScrollEvent
        """
        (g,t,i) = xxx_todo_changeme14
        nl,s,vl = self.pid2ctrls[(g,t,i)]
        p = self.plugin.get_parameter(g,t,i)
        minv = p.get_value_min()
        maxv = p.get_value_max()
        value = int(max(min(value, maxv), minv) + 0.5)
        s.set_value(value) # quantize slider position
        self.plugin.set_parameter_value_direct(g,t,i,value,1)
        self.update_valuelabel(g,t,i)
        return True

class DataEntry(Gtk.Dialog):
    """
    A data entry control meant for numerical input of slider values.
    """
    def __init__(self, xxx_todo_changeme15, parent):
        """
        Initializer.
        """
        (minval,maxval,v) = xxx_todo_changeme15
        Gtk.Dialog.__init__(self,
            "Edit Value",
            parent.get_toplevel(),  
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL),
        )	
        self.label = Gtk.Label("Enter Value:")
        self.edit = Gtk.Entry()
        self.edit.set_text(v)
        s = Gtk.HBox()
        s.pack_start(self.label, expand=False)
        s.pack_start(self.edit)
        self.vbox.pack_start(s, expand=False)
        label = Gtk.Label(prepstr("%s - %s" % (minval,maxval)))
        label.set_alignment(0,0.5)
        self.vbox.pack_start(label, expand=False)
        self.edit.grab_focus()
        self.edit.select_region(1,-1)
        self.show_all()
        self.edit.connect('activate', self.on_text_enter)

    def on_text_enter(self, widget):
	    self.response(Gtk.ResponseType.OK)

class RackPanel(Gtk.VBox):
    """
    Rack panel.

    Displays controls for individual plugins.
    """

    __neil__ = dict(
	    id = 'neil.core.rackpanel',
	    singleton = True,
	    categories = [
		    #'neil.viewpanel',
		    #'view',
	    ]
    )

    __view__ = dict(
		    label = "Rack",
		    stockid = "rack",
		    shortcut = 'F11',
		    order = 11,
    )

    def __init__(self):
        """
        Initialization.
        """
        Gtk.VBox.__init__(self)
        self.panels = {}
        scrollwindow = Gtk.ScrolledWindow()
        scrollwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rowgroup = Gtk.VBox()
        scrollwindow.add_with_viewport(rowgroup)
        self.scrollwindow = scrollwindow
        self.rowgroup = rowgroup
        self.connect('realize', self.on_realize)
        self.add(self.scrollwindow)
        eventbus = com.get('neil.core.eventbus')
        eventbus.zzub_delete_plugin += self.update_all

    def handle_focus(self):
        self.scrollwindow.grab_focus()

    def on_realize(self, widget):
        self.update_all()

    def update_all(self, *args):
        """
        Updates the full view.
        """
        print("rack:update_all")
        addlist, rmlist = diff(list(self.panels.keys()), list(common.get_plugin_infos().keys()))
        for plugin in rmlist:
            self.panels[plugin].destroy()
            del self.panels[plugin]
        for plugin in addlist:
            view = ParameterView(plugin)
            view.show_all()
            self.panels[plugin] = view
            self.rowgroup.pack_start(view, expand=False)
            #~ view.set_size_request(*view.get_best_size())

__neil__ = dict(
	classes = [
		ParameterView,
		RackPanel,
	],
)

