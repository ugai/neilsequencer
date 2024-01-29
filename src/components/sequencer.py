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
Contains all classes and functions needed to render the sequence
editor and its associated components.
"""

if __name__ == '__main__':
    import os
    os.system('../../bin/neil-combrowser neil.core.sequencerpanel')
    raise SystemExit

from gi.repository import GObject, Gtk, Gdk, Pango
import sys
# from neil.utils import PLUGIN_FLAGS_MASK, ROOT_PLUGIN_FLAGS
# from neil.utils import GENERATOR_PLUGIN_FLAGS, EFFECT_PLUGIN_FLAGS
# from neil.utils import CONTROLLER_PLUGIN_FLAGS
from neil.utils import prepstr, get_item_count
from neil.utils import get_clipboard_text, set_clipboard_text, add_scrollbars
from neil.utils import is_effect, is_generator, is_controller
from neil.utils import is_root, get_new_pattern_name
from neil.utils import Menu, wave_names_generator
from neil.utils import cmp
import random
import config
import neil.common as common
MARGIN = common.MARGIN
MARGIN2 = common.MARGIN2
MARGIN3 = common.MARGIN3
MARGIN0 = common.MARGIN0
import neil.com as com
import zzub

SEQKEYS = '0123456789abcdefghijklmnopqrstuvwxyz'
SEQKEYMAP = dict(list(zip(SEQKEYS, list(range(0x10, len(SEQKEYS) + 0x10)))))
SEQKEYMAP[chr(45)] = 0x00
SEQKEYMAP[chr(44)] = 0x01


class PatternNotFoundException(Exception):
    """
    Exception thrown when pattern is not found.
    """
    pass


class AddSequencerTrackDialog(Gtk.Dialog):
    """
    Sequencer Dialog Box.

    This dialog is used to create a new track for an existing machine.
    """
    def __init__(self, parent, machines):
        Gtk.Dialog.__init__(self,
                "Add track",
                parent.get_toplevel(),
                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                None
        )
        self.btnok = self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.btncancel = self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.combo = Gtk.ComboBoxText()
        for machine in sorted(machines, lambda a, b: cmp(a.lower(), b.lower())):
            self.combo.append_text(machine)
        # Set a default.
        self.combo.set_active(0)
        self.vbox.add(self.combo)
        self.show_all()


class SequencerToolBar(Gtk.HBox):
    """
    Sequencer Toolbar

    Allows to set the step size for the sequencer view.
    """
    def __init__(self, seqview):
        """
        Initialization.
        """
        super().__init__(False, MARGIN)
        self.parent = seqview
        self.seqview = seqview
        self.set_border_width(MARGIN)
        self.steplabel = Gtk.Label()
        self.steplabel.set_text_with_mnemonic("_Step")
        self.stepselect = Gtk.ComboBoxText.new_with_entry()
        self.steps = [1, 2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44,
                      48, 52, 56, 60, 64]
        self.stepselect.connect('changed', self.on_stepselect)
        self.stepselect.connect('key_release_event', self.on_stepselect)
        self.stepselect.set_size_request(60, -1)
        self.steplabel.set_mnemonic_widget(self.stepselect)
        # Follow song checkbox.
        self.followsong = Gtk.CheckButton("Follow Song Position")
        self.followsong.set_active(False)
        # Display all the components.
        self.pack_start(self.steplabel, expand=False, fill=False, padding=0)
        self.pack_start(self.stepselect, expand=False, fill=False, padding=0)
        self.pack_start(self.followsong, expand=False, fill=False, padding=0)

    def increase_step(self):
        if self.parent.view.step < 64:
            self.parent.view.step *= 2
        self.update_stepselect()
        self.parent.update_all()

    def decrease_step(self):
        if self.parent.view.step > 1:
            self.parent.view.step /= 2
        self.update_stepselect()
        self.parent.update_all()

    def update_all(self):
        """
        Updates the toolbar to reflect sequencer changes.
        """
        self.update_stepselect()

    def update_stepselect(self):
        """
        Updates the step selection choice box.
        """
        player = com.get('neil.core.player')
        self.stepselect.get_model().clear()
        for i in self.steps:
            self.stepselect.append_text("%i" % i)
        try:
            self.stepselect.set_active(self.steps.index(self.parent.view.step))
            config.get_config().set_default_int('SequencerStep',
                                                self.parent.view.step)
            player.sequence_step = self.parent.view.step
        except ValueError:
            pass
        self.parent.view.adjust_scrollbars()

    def on_stepselect(self, widget, event=False):
        """
        Handles events sent from the choice box when a step size is being selected.
        """
        try:
            step = int(widget.get_active_text())
        except:
            self.parent.view_step = 1
            return
        if widget.get_active() == -1 and event == False:
            return
        if self.parent.view.step == step:
            return
        if (step > 128):
            self.parent.view.step = 128
        if (step < 1):
            self.parent.view.step = 1
        else:
            self.parent.view.step = step
        self.parent.update_all()
        player = com.get('neil.core.player')
        player.set_seqstep(step)


class SequencerPanel(Gtk.VBox):
    """
    Sequencer pattern panel.

    Displays all the patterns available for the current track.
    """
    __neil__ = dict(
        id = 'neil.core.sequencerpanel',
        singleton = True,
        categories = [
            'neil.viewpanel',
            'view',
        ]
    )

    __view__ = dict(
        label = "Sequencer",
        stockid = "neil_sequencer",
        shortcut = 'F4',
        order = 4,
    )

    def __init__(self):
        """
        Initialization.
        """
        Gtk.VBox.__init__(self)
        self.splitter = Gtk.HPaned()
        self.seqliststore = Gtk.ListStore(str, str)
        self.seqpatternlist = Gtk.TreeView(self.seqliststore)
        self.seqpatternlist.set_rules_hint(True)
        self.seqpatternlist.connect("button-press-event",
                                    self.on_pattern_list_button)
        self.seqpatternlist.connect("enter-notify-event",
                                    self.on_mouse_over)
        self.seqpatternlist.connect("row-activated", self.on_visit_pattern)
        tvkey = Gtk.TreeViewColumn("Key")
        tvkey.set_resizable(True)
        tvpname = Gtk.TreeViewColumn("Pattern Name")
        tvpname.set_resizable(True)
        cellkey = Gtk.CellRendererText()
        cellpname = Gtk.CellRendererText()
        tvkey.pack_start(cellkey, expand=False)
        tvpname.pack_start(cellpname, expand=False)
        tvkey.add_attribute(cellkey, 'text', 0)
        tvpname.add_attribute(cellpname, 'text', 1)
        self.seqpatternlist.append_column(tvkey)
        self.seqpatternlist.append_column(tvpname)
        self.seqpatternlist.set_search_column(0)
        tvkey.set_sort_column_id(0)
        tvpname.set_sort_column_id(1)

        vscroll = Gtk.VScrollbar()
        hscroll = Gtk.HScrollbar()

        self.seqview = SequencerView(self, hscroll, vscroll)
        self.seqview.connect("enter-notify-event",
                             self.on_mouse_over)
        self.viewport = Gtk.Viewport()
        self.viewport.add(self.seqview)
        scrollwin = Gtk.Table(2, 2)
        scrollwin.attach(self.viewport, 0, 1, 0, 1,
                         Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND, Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND)
        scrollwin.attach(vscroll, 1, 2, 0, 1, 0, Gtk.AttachOptions.FILL)
        scrollwin.attach(hscroll, 0, 1, 1, 2, Gtk.AttachOptions.FILL, 0)

        self.splitter.pack1(add_scrollbars(self.seqpatternlist), False, False)
        self.splitter.pack2(scrollwin, True, True)
        self.view = self.seqview
        self.toolbar = SequencerToolBar(self)

        self.statusbar = Gtk.HBox(False, MARGIN)
        self.statusbar.set_border_width(MARGIN0)

        self.pack_start(self.toolbar, expand=False, fill=False, padding=0)
        self.pack_start(self.splitter, expand=False, fill=False, padding=0)
        self.pack_end(self.statusbar, expand=False, fill=False, padding=0)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade
        self.update_list()
        self.toolbar.update_all()
        self.seqview.connect('size-allocate', self.on_sash_pos_changed)
        #self.seqview.grab_focus()
        eventbus = com.get('neil.core.eventbus')
        eventbus.edit_sequence_request += self.edit_sequence_request

    def on_visit_pattern(self, treeview, treeiter, path):
        pattern = treeiter[0] - 2
        if pattern < 0:
            return
        else:
            self.seqview.jump_to_pattern(self.plugin, pattern)

    def on_pattern_list_button(self, treeview, event):
        def on_create(item):
            from patterns import show_pattern_dialog
            from patterns import DLGMODE_NEW
            from neil.utils import get_new_pattern_name
            result = show_pattern_dialog(treeview,
                                         get_new_pattern_name(self.plugin),
                                         self.seqview.step, DLGMODE_NEW, False)
            if result == None:
                return
            else:
                name, length, switch = result
                plugin = self.plugin
                pattern = plugin.create_pattern(length)
                pattern.set_name(name)
                plugin.add_pattern(pattern)
                player = com.get('neil.core.player')
                player.history_commit("new pattern")

        def on_clone(item, pattern):
            from patterns import show_pattern_dialog
            from patterns import DLGMODE_COPY
            from neil.utils import get_new_pattern_name
            result = show_pattern_dialog(treeview,
                                         get_new_pattern_name(self.plugin),
                                         self.seqview.step, DLGMODE_COPY, False)
            if result == None:
                return
            else:
                name, patternsize, switch = result
                m = self.plugin
                p = m.get_pattern(pattern)
                p.set_name(name)
                m.add_pattern(p)
                player = com.get('neil.core.player')
                player.history_commit("clone pattern")

        def on_rename(item, pattern):
            from patterns import show_pattern_dialog
            from patterns import DLGMODE_CHANGE
            from neil.utils import get_new_pattern_name
            result = show_pattern_dialog(treeview,
                                         self.plugin.get_pattern_name(pattern),
                                         self.plugin.get_pattern_length(pattern),
                                         DLGMODE_CHANGE, False)
            if result == None:
                return
            else:
                name, length, switch = result
                plugin = self.plugin
                plugin.set_pattern_name(pattern, name)
                plugin.set_pattern_length(pattern, length)
                player = com.get('neil.core.player')
                player.history_commit("change pattern properties")
            self.view.redraw()

        def on_clear(item, pattern):
            plugin = self.plugin
            length = plugin.get_pattern_length(pattern)
            name = plugin.get_pattern_name(pattern)
            new_pattern = plugin.create_pattern(length)
            new_pattern.set_name(name)
            plugin.update_pattern(pattern, new_pattern)
            player = com.get('neil.core.player')
            player.history_commit("clear pattern")

        def on_delete(item, pattern):
            plugin = self.plugin
            if pattern >= 0:
                plugin.remove_pattern(pattern)
                player = com.get('neil.core.player')
                player.history_commit("remove pattern")
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            path = treeview.get_path_at_pos(x, y)
            menu = Gtk.Menu()
            new = Gtk.MenuItem("New pattern")
            clone = Gtk.MenuItem("Clone pattern")
            rename = Gtk.MenuItem("Pattern properties")
            clear = Gtk.MenuItem("Clear pattern")
            delete = Gtk.MenuItem("Delete pattern")
            menu.append(new)
            new.connect('activate', on_create)
            menu.append(clone)
            menu.append(rename)
            menu.append(clear)
            menu.append(delete)
            if hasattr(self, 'plugin') and self.plugin != None:
                new.show()
            if path != None:
                clone.connect('activate', on_clone, path[0][0] - 2)
                clone.show()
                rename.connect('activate', on_rename, path[0][0] - 2)
                rename.show()
                clear.connect('activate', on_clear, path[0][0] - 2)
                clear.show()
                delete.connect('activate', on_delete, path[0][0] - 2)
                delete.show()
            if hasattr(self, 'plugin') and self.plugin != None:
                menu.popup(None, None, None, event.button, event.time)

    def on_mouse_over(self, widget, event):
        widget.grab_focus()

    def edit_sequence_request(self, track=None, row=None):
        framepanel = com.get('neil.core.framepanel')
        framepanel.select_viewpanel(self)
        #TODO: add active_tracks option to allow track, row position change
        #player.active_tracks = [(track, row)]
        #framepanel = com.get('neil.core.framepanel')
        #framepanel.select_viewpanel(self)

    def handle_focus(self):
        self.view.needfocus = True

    def update_all(self):
        """
        Updates everything to reflect changes in the sequencer.
        """
        self.update_list()
        self.toolbar.update_all()
        for k, v in self.view.plugin_info.items():
            v.patterngfx = {}
        self.view.update()
        self.seqview.set_cursor_pos(0, 0)
        self.seqview.adjust_scrollbars()
        self.seqview.redraw()
        self.seqview.adjust_scrollbars()

    def update_list(self):
        """
        Updates the panel to reflect a sequence view change.
        """
        self.seqliststore.clear()
        self.seqliststore.append(['-', 'Mute'])
        self.seqliststore.append([',', 'Break'])
        track = self.seqview.get_track()
        if track:
            for pattern, key in zip(track.get_plugin().get_pattern_list(),
                                    SEQKEYS):
                self.seqliststore.append([key, pattern.get_name()])
            self.plugin = track.get_plugin()

    def on_sash_pos_changed(self, widget, *args):
        """
        Sent when the sash position changes.

        @param event: Event.
        @type event: wx.Event
        """
        if not self.splitter.window:
            return
        if not self.splitter.window.is_visible():
            return
        config.get_config().save_window_pos("SequencerSplitter", self.splitter)

    def __set_properties(self):
        """
        Sets properties during initialization.
        """
        # begin wxGlade: SequencerFrame.__set_properties
        self.statuslabels = []
        label = Gtk.Label()
        self.statuslabels.append(label)
        self.statusbar.pack_start(label, expand=False, fill=False, padding=0)
        self.statusbar.pack_start(Gtk.VSeparator(), expand=False, fill=False, padding=0)
        label = Gtk.Label()
        self.statuslabels.append(label)
        self.statusbar.pack_start(label, expand=False, fill=False, padding=0)
        self.statusbar.pack_start(Gtk.VSeparator(), expand=False, fill=False, padding=0)
        # end wxGlade

    def __do_layout(self):
        """
        Arranges children components during initialization.
        """
        self.show_all()
        config.get_config().load_window_pos("SequencerSplitter", self.splitter)
        # end wxGlade

# end of class SequencerFrame


class SequencerView(Gtk.DrawingArea):
    """
    Sequence viewer class.
    """
    CLIPBOARD_SEQUENCER = "SEQUENCERDATA"

    def __init__(self, panel, hscroll, vscroll):
        """
        Initialization.
        """
        self.panel = panel
        self.hscroll = hscroll
        self.vscroll = vscroll

        self.needfocus = True

        # Variables that were previously defined as constants.
        self.seq_track_size = 36
        self.seq_step = 16
        self.seq_left_margin = 96
        self.seq_top_margin = 20
        self.seq_row_size = 38

        self.plugin_info = common.get_plugin_infos()
        player = com.get('neil.core.player')
        self.playpos = player.get_position()
        self.row = 0
        self.track = 0
        self.startseqtime = 0
        self.starttrack = 0
        self.step = config.get_config().get_default_int('SequencerStep',
                                                        self.seq_step)
        self.wmax = 0
        player.set_loop_end(self.step)
        self.selection_start = None
        self.selection_end = None
        self.dragging = False
        Gtk.DrawingArea.__init__(self)
        self.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
        self.set_property('can-focus', True)
        self.connect("draw", self.expose)
        self.connect('key-press-event', self.on_key_down)
        self.connect('button-press-event', self.on_left_down)
        self.connect('motion-notify-event', self.on_motion)
        self.connect('button-release-event', self.on_left_up)
        self.connect('scroll-event', self.on_mousewheel)
        self.hscroll.connect('change-value', self.on_hscroll_window)
        self.vscroll.connect('change-value', self.on_vscroll_window)
        GObject.timeout_add(100, self.update_position)
        eventbus = com.get('neil.core.eventbus')
        eventbus.zzub_sequencer_changed += self.redraw
        eventbus.zzub_set_sequence_event += self.redraw
        eventbus.document_loaded += self.redraw
        set_clipboard_text("invalid_clipboard_data")

    def track_row_to_pos(self, xxx_todo_changeme):
        """
        Converts track and row to a pixel coordinate.

        @param track: Track index.
        @type track: int
        @param row: Row index.
        @type row: int
        @return: Pixel coordinate.
        @rtype: (int, int)
        """
        (track, row) = xxx_todo_changeme
        if row == -1:
            x = 0
        else:
            x = int((((float(row) - self.startseqtime) / self.step) *
                     self.seq_row_size) + self.seq_left_margin + 0.5)
        if track == -1:
            y = 0
        else:
            y = (((track - self.starttrack) * self.seq_track_size) +
                 self.seq_top_margin)
        return x, y

    def pos_to_track_row(self, xxx_todo_changeme1):
        """
        Converts pixel coordinate to a track and row.

        @param x: Pixel coordinate.
        @type x: int
        @param y: Pixel coordinate.
        @type y: int
        @return: Tuple containing track and row index.
        @rtype: (int, int)
        """
        (x, y) = xxx_todo_changeme1
        if x < self.seq_left_margin:
            row = -1
        else:
            row = (((x - self.seq_left_margin) / self.seq_row_size) * self.step) + self.startseqtime
        if y < self.seq_top_margin:
            track = -1
        else:
            track = ((y - self.seq_top_margin) / self.seq_track_size) + self.starttrack
        return track, row

    def get_endtrack(self):
        """
        Get the last visible track.
        """
        w, h = self.get_client_size()
        return self.pos_to_track_row((0, h))[0]

    def get_endrow(self):
        """
        Get the last visible row.
        """
        w, h = self.get_client_size()
        return self.pos_to_track_row((w, 0))[1]

    def set_cursor_pos(self, track, row):
        """
        Updates the cursor position to a track and row.

        @param track: Pattern index.
        @type track: int
        @param row: Row index.
        @type row: int
        """
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        track = max(min(track, seq.get_sequence_track_count() - 1), 0)
        row = max(row, 0)
        if (track, row) == (self.track, self.row):
            return
        if self.track != track:
            self.track = track
            endtrack = self.get_endtrack()
            if self.track >= endtrack:
                while self.track >= endtrack:
                    self.starttrack += 1
                    endtrack = self.get_endtrack()
                self.redraw()
            elif self.track < self.starttrack:
                while self.track < self.starttrack:
                    self.starttrack -= 1
                self.redraw()
            self.panel.update_list()
        if self.row != row:
            self.row = row
            endrow = self.get_endrow()
            if self.row >= endrow:
                while self.row >= endrow:
                    self.startseqtime += self.step
                    endrow = self.get_endrow()
                self.redraw()
            elif self.row < self.startseqtime:
                while self.row < self.startseqtime:
                    self.startseqtime -= self.step
                self.redraw()
        self.panel.statuslabels[0].set_label(prepstr('%s' % (self.row)))
        t = self.get_track()
        if t:
            plugin = t.get_plugin()
            self.panel.statuslabels[1].set_label(prepstr('%s' % (plugin.get_name())))
        else:
            self.panel.statuslabels[1].set_label("")
        self.redraw()

    def get_track(self):
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        if (self.track != -1) and (self.track < seq.get_sequence_track_count()):
            return seq.get_sequence(self.track)
        return None

    # FIXME why does this fail when master is the only plugin and no patterns exist?
    def create_track(self, plugin):
        # get sequencer and add the track
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        track = seq.create_sequence(plugin, zzub.zzub_sequence_type_pattern)
        # if it has no existing patterns, make one (even if it has no parameters, it might have incoming connections)
        if plugin.get_pattern_count() == 0:
            pattern = plugin.create_pattern(player.sequence_step)
            pattern.set_name('00')
            plugin.add_pattern(pattern)
            # add a pattern trigger-event
            track.set_event(0, 16)
        player.history_commit("add track")
        self.adjust_scrollbars()
        self.redraw()

    def insert_at_cursor(self, index = -1):
        """
        Inserts a space at cursor.
        """
        player = com.get('neil.core.player')
        t = self.get_track()
        if not t:
            return
        if index != -1:
            pcount = t.get_plugin().get_pattern_count()
            t.set_event(self.row, min(index, 0x10 + pcount - 1))
        else:
            t.insert_events(self.row, self.step)
        player.history_commit("insert sequence")

    def delete_at_cursor(self):
        """
        Deletes pattern at cursor.
        """
        player = com.get('neil.core.player')
        t = player.get_sequence(self.track)
        t.remove_events(self.row, self.step)
        player.history_commit("delete sequences")

    def selection_range(self):
        player = com.get('neil.core.player')
        start = (min(self.selection_start[0], self.selection_end[0]),
                                min(self.selection_start[1], self.selection_end[1]))
        end = (max(self.selection_start[0], self.selection_end[0]),
                                max(self.selection_start[1], self.selection_end[1]))
        for track in range(start[0], end[0] + 1):
            t = player.get_sequence(track)
            events = dict(t.get_event_list())
            for row in range(start[1], end[1] + 1):
                if row in events:
                    yield track, row, events[row]
                else:
                    yield track, row, -1

    def unpack_clipboard_data(self, d):
        """
        Unpacks clipboard data

        @param d: Data that is to be unpacked.
        @type d: unicode
        """
        magic, d = d[:len(self.CLIPBOARD_SEQUENCER)], d[len(self.CLIPBOARD_SEQUENCER):]
        if magic != self.CLIPBOARD_SEQUENCER:
            raise ValueError
        while d:
            track, d = int(d[:4], 16), d[4:]
            row, d = int(d[:8], 16), d[8:]
            value, d = int(d[:4], 16), d[4:]
            yield track, row, value

    def on_popup_copy(self, *args):
        """
        Copies the current selection into the clipboard
        """
        #print self.selection_start, self.selection_end
        if self.selection_start == None:
            return
        data = self.CLIPBOARD_SEQUENCER
        startrow = min(self.selection_start[1], self.selection_end[1])
        for track, row, value in self.selection_range():
            data += "%04x%08x%04x" % (track, row - startrow, value)
        set_clipboard_text(data)

    def on_popup_create_pattern(self, *args):
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        if not self.selection_start:
            self.selection_start = (self.track, self.row)
            self.selection_end = (self.track, self.row)
        try:
            start = (min(self.selection_start[0], self.selection_end[0]),
                     min(self.selection_start[1], self.selection_end[1]))
            end = (max(self.selection_start[0], self.selection_end[0]),
                   max(self.selection_start[1], self.selection_end[1]))
        except TypeError:
            # There is no selection.
            return
        for t in seq.get_track_list()[start[0]:end[0] + 1]:
            m = t.get_plugin()
            patternsize = end[1] + self.step - start[1]
            name = get_new_pattern_name(m)
            p = m.create_pattern(patternsize)
            p.set_name(name)
            m.add_pattern(p)
            for i in range(m.get_pattern_count()):
                pattern = m.get_pattern(i)
                if pattern.get_name() == name:
                    t.set_event(start[1], 0x10 + i)
                    break
            player.history_commit("new pattern")

    def on_popup_clone_pattern(self, *args):
        """Create a copy of the pattern at cursor and replace the current one.
        """
        from neil.utils import get_new_pattern_name
        player = com.get('neil.core.player')
        machine, pattern_id, _ = self.get_pattern_at(self.track, self.row, includespecial=True)
        if pattern_id is not None:
            pattern_id -= 0x10
            name = get_new_pattern_name(machine)
            pattern = machine.get_pattern(pattern_id)
            pattern.set_name(name)
            machine.add_pattern(pattern)
            self.insert_at_cursor(machine.get_pattern_count() + 0x10 - 1)
            player.history_commit("clone pattern")
        
    def on_popup_merge(self, *args):
        player = com.get('neil.core.player')
        player.set_callback_state(False)
        seq = player.get_current_sequencer()
        try:
            start = (min(self.selection_start[0], self.selection_end[0]),
                     min(self.selection_start[1], self.selection_end[1]))
            end = (max(self.selection_start[0], self.selection_end[0]),
                   max(self.selection_start[1], self.selection_end[1]))
        except TypeError:
            # There is no selection.
            return
        for t in seq.get_track_list()[start[0]:(end[0] + 1)]:
            patternsize = 0
            eventlist = []
            m = t.get_plugin()
            for time, value in t.get_event_list():
                if (time >= start[1]) and (time < (end[1] + self.step)):
                    if value >= 0x10:
                        value -= 0x10
                        # copy contents between patterns
                        eventlist.append((time, m.get_pattern(value)))
                        patternsize = max(patternsize, time - start[1] +
                                          m.get_pattern(value).get_row_count())
            if patternsize:
                name = get_new_pattern_name(m)
                p = m.create_pattern(patternsize)
                p.set_name(name)
                #m.add_pattern(p)
                group_track_count = [m.get_input_connection_count(),
                                     1, m.get_track_count()]
                for time, pattern in eventlist:
                    t.set_event(time, -1)
                    for r in range(pattern.get_row_count()):
                        rowtime = time - start[1] + r
                        for g in range(3):
                            for ti in range(group_track_count[g]):
                                for i in range(m.get_pluginloader().\
                                                    get_parameter_count(g)):
                                    p.set_value(rowtime, g, ti, i,
                                                pattern.get_value(r, g, ti, i))
                m.add_pattern(p)
                for i in range(m.get_pattern_count()):
                    if m.get_pattern(i).get_name() == name:
                        t.set_event(start[1], 0x10 + i)
                        break
        player.history_commit("merge patterns")
        player.set_callback_state(True)
        eventbus = com.get('neil.core.eventbus')
        eventbus.document_loaded()

    def on_popup_cut(self, *args):
        self.on_popup_copy(*args)
        self.on_popup_delete(*args)

    # FIXME it would be nice if pasting moved the cursor forward, so that
    # repeated pasting would work
    def on_popup_paste(self, *args):
        player = com.get('neil.core.player')
        player.set_callback_state(False)
        seq = player.get_current_sequencer()
        data = get_clipboard_text()            
        try:
            for track, row, value in self.unpack_clipboard_data(data.strip()):
                t = seq.get_sequence(track)
                if value == -1:
                    t.set_event(self.row + row, -1)
                else:
                    t.set_event(self.row + row, value)
            player.history_commit("paste selection")
        except ValueError:
            pass
        player.set_callback_state(True)
        eventbus = com.get('neil.core.eventbus')
        eventbus.document_loaded()

    def on_popup_delete(self, *args):
        player = com.get('neil.core.player')
        player.set_callback_state(False)
        seq = player.get_current_sequencer()
        #print self.selection_start
        try:
            start = (min(self.selection_start[0], self.selection_end[0]),
                     min(self.selection_start[1], self.selection_end[1]))
            end = (max(self.selection_start[0], self.selection_end[0]),
                   max(self.selection_start[1], self.selection_end[1]))
        except TypeError:
            # There is no selection.
            return
        for track in range(start[0], end[0] + 1):
            t = seq.get_sequence(track)
            for row in range(start[1], end[1] + 1):
                t.set_event(row, -1)
        player.history_commit("delete selection")
        player.set_callback_state(True)
        eventbus = com.get('neil.core.eventbus')
        eventbus.document_loaded()

    def on_popup_delete_track(self, *args):
        """
        Callback that handles track deletion via the popup menu

        @param event: Menu event.
        @type event: wx.CommandEvent
        """
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        t = seq.get_track_list()[self.track]
        t.destroy()
        track_count = seq.get_sequence_track_count()
        player.history_commit("delete track")
        # moves cursor if beyond existing tracks
        if self.track > track_count - 1:
            self.set_cursor_pos(track_count - 1, self.row)
        self.adjust_scrollbars()
        self.redraw()

    def on_popup_add_track(self, widget, plugin):
        """
        Callback that handles track addition via the popup menu

        @param event: Menu event.
        @type event: wx.CommandEvent
        """
        self.create_track(plugin)

    def on_popup_record_to_wave(self, widget, index):
        """
        Callback that is used to record a looped song section
        to an instrument slot.
        """
        player = com.get('neil.core.player')
        loader = player.get_pluginloader_by_name('@zzub.org/recorder/wavetable')
        if not loader:
            print("Can't find instrument recorder plugin loader.", file=sys.stderr)
            return
        flags = zzub.zzub_plugin_flag_no_undo | zzub.zzub_plugin_flag_no_save
        recorder = zzub.Player.create_plugin(player, None, 0, "_IRecorder", loader, flags)
        if not recorder:
            print("Can't create instrument recorder plugin instance.", file=sys.stderr)
            return
        master = player.get_plugin(0)
        recorder.add_input(master, zzub.zzub_connection_type_audio)
        player.set_machine_non_song(recorder, True)
        recorder.set_parameter_value(zzub.zzub_parameter_group_global, 0, 0, index, False)
        recorder.set_parameter_value(zzub.zzub_parameter_group_global, 0, 1, 1, False)
        old_song_end = player.get_song_end()
        old_position = player.get_position()
        old_loop_enabled = player.get_loop_enabled()
        player.set_song_end(player.get_loop_end())
        player.set_position(player.get_loop_start())
        player.set_loop_enabled(0)
        player.play()
        dialog = Gtk.Dialog(
            "Recording",
            buttons=(Gtk.STOCK_OK, True)
            )
        dialog.vbox.add(Gtk.Label("Press OK when the recording is done."))
        dialog.show_all()
        dialog.run()
        recorder.destroy()
        dialog.destroy()
        player.set_song_end(old_song_end)
        player.set_position(old_position)
        player.set_loop_enabled(old_loop_enabled)
        player.flush(None, None)
        player.history_flush_last()

    def on_context_menu(self, event):
        """
        Callback that constructs and displays the popup menu

        @param event: Menu event.
        @type event: wx.CommandEvent
        """
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        x, y = int(event.x), int(event.y)
        track, row = self.pos_to_track_row((x, y))
        self.set_cursor_pos(max(min(track, seq.get_sequence_track_count()), 0), self.row)
        if self.selection_start != None:
            sel_sensitive = True
        else:
            sel_sensitive = False
        if get_clipboard_text().startswith(self.CLIPBOARD_SEQUENCER):
            paste_sensitive = True
        else:
            paste_sensitive = False
        menu = Menu()
        pmenu = Menu()
        wavemenu = Menu()
        for plugin in sorted(list(player.get_plugin_list()), lambda a, b: cmp(a.get_name().lower(), b.get_name().lower())):
            pmenu.add_item(prepstr(plugin.get_name().replace("_", "__")), self.on_popup_add_track, plugin)
        for i, name in enumerate(wave_names_generator()):
            wavemenu.add_item_no_underline(name, self.on_popup_record_to_wave, i + 1)
        menu.add_submenu("Add track", pmenu)
        menu.add_item("Delete track", self.on_popup_delete_track)
        menu.add_separator()
        menu.add_item("Set loop start", self.set_loop_start)
        menu.add_item("Set loop end", self.set_loop_end)
        menu.add_separator()
        menu.add_submenu("Record loop", wavemenu)
        menu.add_separator()
        menu.add_item("Cut", self.on_popup_cut).set_sensitive(sel_sensitive)
        menu.add_item("Copy", self.on_popup_copy).set_sensitive(sel_sensitive)
        menu.add_item("Paste", self.on_popup_paste).set_sensitive(paste_sensitive)
        menu.add_item("Delete", self.on_popup_delete).set_sensitive(sel_sensitive)
        menu.add_separator()
        menu.add_item("Create pattern", self.on_popup_create_pattern)
        menu.add_item("Clone pattern", self.on_popup_clone_pattern)
        menu.add_item("Merge patterns", self.on_popup_merge).set_sensitive(sel_sensitive)
        menu.show_all()
        menu.attach_to_widget(self, None)
        menu.popup(self, event)

    def show_plugin_dialog(self):
        pmenu = []
        player = com.get('neil.core.player')
        for plugin in player.get_plugin_list():
            pmenu.append(prepstr(plugin.get_name()))
        dlg = AddSequencerTrackDialog(self, pmenu)
        response = dlg.run()
        dlg.hide_all()
        if response == Gtk.ResponseType.OK:
            name = dlg.combo.get_active_text()
            for plugin in player.get_plugin_list():
                if plugin.get_name() == name:
                    self.create_track(plugin)
                    break
        dlg.destroy()

    def set_loop_start(self, *args):
        """
        Set loop startpoint
        """
        player = com.get('neil.core.player')
        player.set_loop_start(self.row)
        if player.get_loop_end() <= self.row:
            player.set_loop_end(self.row + self.step)
        self.redraw()

    def set_loop_end(self, *args):
        player = com.get('neil.core.player')
        pos = self.row  # + self.step
        if player.get_loop_end() != pos:
            player.set_loop_end(pos)
            if pos > player.get_song_end():
                player.set_song_end(pos)
            if player.get_loop_start() >= pos:
                player.set_loop_start(0)
        else:
            player.set_song_end(pos)
        self.redraw()

    def on_key_down(self, widget=None, event=None):
        """
        Callback that responds to key stroke in sequence view.

        @param event: Key event
        @type event: wx.KeyEvent
        """
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        mask = event.state
        kv = event.keyval
        # convert keypad numbers
        if Gdk.keyval_from_name('KP_0') <= kv <= Gdk.keyval_from_name('KP_9'):
            kv = kv - Gdk.keyval_from_name('KP_0') + Gdk.keyval_from_name('0')
        k = Gdk.keyval_name(event.keyval)
        #print kv, k, event.keyval
        arrow_down = k in ['Left', 'Right', 'Up', 'Down', 'KP_Left', 'KP_Right', 'KP_Up', 'KP_Down']
        is_selecting = arrow_down and (mask & Gdk.SHIFT_MASK)
        if is_selecting:
            # starts the selection if nothing selected
            if self.selection_start == None:
                self.selection_start = (self.track, self.row)
        elif arrow_down:
            self.deselect()
        if mask & Gdk.SHIFT_MASK and (k in ('KP_Add', 'plus', 'asterisk')):
            self.panel.toolbar.increase_step()
            self.set_cursor_pos(self.track, self.row)
        elif mask & Gdk.SHIFT_MASK and (k in ('KP_Subtract', 'underscore')):
            self.panel.toolbar.decrease_step()
            self.set_cursor_pos(self.track, self.row)
        elif (mask & Gdk.CONTROL_MASK):
            if k == 'Return':
                self.show_plugin_dialog()
            elif k == 'Delete':
                self.on_popup_delete_track(event)
                self.adjust_scrollbars()
            elif k == 'b':
                self.set_loop_start()
            elif k == 'e':
                self.set_loop_end()
            elif k == 'l':
                t = self.get_track()
                if t:
                    mp = t.get_plugin()
                    player.solo(mp)
                    self.redraw()
            elif k == 'i':
                for track in seq.get_track_list():
                    track.insert_events(self.row, self.step)
                player.history_commit("insert event")
            elif k == 'd':
                for track in seq.get_track_list():
                    track.remove_events(self.row, self.step)
                player.history_commit("remove event")
            elif k == 'c':
                self.on_popup_copy()
            elif k == 'x':
                self.on_popup_cut()
            elif k == 'v':
                self.on_popup_paste()
            elif k == 'Up' or k == 'KP_Up':
                if self.track > 0:
                    t = seq.get_track_list()[self.track]
                    t.move(self.track - 1)
                    self.track -= 1
                    player.history_commit("move track")
                    self.redraw()
            elif k == 'Down' or k == 'KP_Down':
                if self.track < (seq.get_sequence_track_count() - 1):
                    t = seq.get_track_list()[self.track]
                    t.move(self.track + 1)
                    self.track += 1
                    player.history_commit("move track")
                    self.redraw()
            elif k == 'Left' or k == 'KP_Left':
                self.set_cursor_pos(self.track, self.row - (self.step * 16))
            elif k == 'Right' or k == 'KP_Right':
                self.set_cursor_pos(self.track, self.row + (self.step * 16))
            else:
                return False
        elif k == 'Left' or k == 'KP_Left':
            self.set_cursor_pos(self.track, self.row - self.step)
            self.adjust_scrollbars()
        elif k == 'Right' or k == 'KP_Right':
            pass
            self.set_cursor_pos(self.track, self.row + self.step)
            self.adjust_scrollbars()
        elif k == 'Up' or k == 'KP_Up':
            self.set_cursor_pos(self.track - 1, self.row)
            self.adjust_scrollbars()
        elif k == 'Down' or k == 'KP_Down':
            self.set_cursor_pos(self.track + 1, self.row)
            self.adjust_scrollbars()
        elif ((kv < 256) and (chr(kv).lower() in SEQKEYMAP) and
              self.selection_start == None and self.selection_end == None):
            idx = SEQKEYMAP[chr(kv).lower()]
            t = self.get_track()
            if t:
                mp = t.get_plugin()
                if (idx < 0x10) or ((idx - 0x10) < mp.get_pattern_count()):
                    if (idx >= 0x10):
                        newrow = self.row + mp.get_pattern(idx - 0x10).get_row_count()
                        newrow = newrow - (newrow % self.step)
                    else:
                        newrow = self.row + self.step
                    self.insert_at_cursor(idx)
                    player.history_commit("add pattern reference")
                    self.set_cursor_pos(self.track, newrow)
                    #print self.track, self.row
                    self.adjust_scrollbars()
        elif k == 'space':  # space
            spl = self.panel.seqpatternlist
            store, row = spl.get_selection().get_selected_rows()
            row = (row and row[0][0]) or 0
            sel = min(max(row, 0), get_item_count(spl.get_model()) - 1)
            if sel >= 2:
                sel = sel - 2 + 0x10
            self.insert_at_cursor(sel)
            self.set_cursor_pos(self.track, self.row + self.step)
        elif k == 'Delete':
            self.delete_at_cursor()
            self.adjust_scrollbars()
        elif k == 'Insert' or  k == 'KP_Insert':
            self.insert_at_cursor()
            self.adjust_scrollbars()
        elif k == 'period':  # dot
            m, pat, bp = self.get_pattern_at(self.track, self.row, includespecial=True)
            if pat != None:
                if pat >= 0x10:
                    pat = m.get_pattern(pat - 0x10)
                    length = pat.get_row_count()
                else:
                    length = self.step
            else:
                length = 0
            if (self.row < (bp + length)):
                newrow = bp + length
                t = seq.get_sequence(self.track)
                t.set_event(bp, -1)
                player.history_commit("remove pattern reference")
                self.set_cursor_pos(self.track, newrow - (newrow % self.step))
            else:
                self.set_cursor_pos(self.track, self.row + self.step)
        elif k == 'Home' or k == 'KP_Home':
            self.set_cursor_pos(self.track, 0)
        elif k == 'End' or k == 'KP_End':
            self.set_cursor_pos(self.track, player.get_song_end() - self.step)
        elif k == 'Page_Up' or k == 'KP_Page_Up':
            spl = self.panel.seqpatternlist
            store, sel = spl.get_selection().get_selected_rows()
            sel = (sel and sel[0][0]) or 0
            sel = min(max(sel - 1, 0), get_item_count(spl.get_model()) - 1)
            spl.get_selection().select_path((sel,))
        elif k == 'Page_Down' or k == 'KP_Page_Down':
            spl = self.panel.seqpatternlist
            store, sel = spl.get_selection().get_selected_rows()
            sel = (sel and sel[0][0]) or 0
            sel = min(max(sel + 1, 0), get_item_count(spl.get_model()) - 1)
            spl.get_selection().select_path((sel,))
        elif k == 'Return':
            m, index, bp = self.get_pattern_at(self.track, self.row)
            if index == None:
                track = self.get_track()
                if track:
                    self.jump_to_pattern(track.get_plugin())
                return
            self.jump_to_pattern(m, index)
        else:
            return False
        # update selection after cursor movement
        if is_selecting:
            self.selection_end = (self.track, self.row)
            self.redraw()
        return True

    def jump_to_pattern(self, plugin, index=0):
        """
        Views a pattern in the pattern view.

        @param plugin: Plugin.
        @type plugin: zzub.Plugin
        @param index: Pattern index.
        @type index: int
        """
        eventbus = com.get('neil.core.eventbus')
        eventbus.edit_pattern_request(plugin, index)

    def get_pattern_at(self, track, row, includespecial=False):
        """
        Gets the pattern and plugin given a sequencer track and row.

        @param track: Track index.
        @type track: int
        @param row: Row index.
        @type row: int
        @return: Tuple containing plugin and pattern index.
        @rtype: (zzub.Plugin, int)
        """
        track = self.get_track()
        if not track:
            return None, None, -1
        plugin = track.get_plugin()
        bestmatch = None
        bestpos = row
        event_list = track.get_event_list()
        for pos, value in event_list:
            if pos > row:
                break
            elif includespecial:
                bestpos = pos
                bestmatch = value
            elif (value >= 0x10):
                bestpos = pos
                bestmatch = value - 0x10
        pattern = plugin.get_pattern(value - 0x10)
        nrows = pattern.get_row_count()
        if pos + nrows < row + 1:
            return plugin, None, -1
        else:
            return plugin, bestmatch, bestpos

    def deselect(self):
        """
        Deselects the current selection.
        """
        if self.selection_end != None:
            self.dragging = False
            self.selection_end = None
            self.selection_start = None
            self.redraw()

    def on_mousewheel(self, widget, event):
        """
        Callback that responds to mousewheeling in sequencer.

        @param event: Mouse event
        @type event: wx.MouseEvent
        """
        if event.state & Gdk.CONTROL_MASK:
            if event.direction == Gdk.SCROLL_DOWN:
                self.panel.toolbar.increase_step()
                self.set_cursor_pos(self.track, self.row)
            elif event.direction == Gdk.SCROLL_UP:
                self.panel.toolbar.decrease_step()
                self.set_cursor_pos(self.track, self.row)
        elif event.direction == Gdk.SCROLL_UP:
            self.set_cursor_pos(self.track, self.row - self.step)
        elif event.direction == Gdk.SCROLL_DOWN:
            self.set_cursor_pos(self.track, self.row + self.step)

    def on_left_down(self, widget, event):
        """
        Callback that responds to left click down in sequence view.

        @param event: Mouse event
        @type event: wx.MouseEvent
        """
        self.grab_focus()
        player = com.get('neil.core.player')
        track_count = player.get_sequence_track_count()
        x, y = int(event.x), int(event.y)
        track, row = self.pos_to_track_row((x, y))
        if event.button == 1:
            if track < track_count:
                if track == -1:
                    player.set_position(max(row, 0))
                elif row == -1:
                    mp = player.get_sequence(track).get_plugin()
                    player.toggle_mute(mp)
                    self.redraw()
                else:
                    self.set_cursor_pos(track, row)
                    self.deselect()
                    self.dragging = True
                    self.grab_add()
            if event.type == Gdk._2BUTTON_PRESS:  # double-click
                m, index, bp = self.get_pattern_at(self.track, self.row)
                if index == None:
                    track = self.get_track()
                    if track:
                        self.jump_to_pattern(track.get_plugin())
                        return
                    self.jump_to_pattern(m, index)

        elif event.button == 3:
            if (x < self.seq_left_margin) and (track < track_count):
                mp = player.get_sequence(track).get_plugin()
                menu = com.get('neil.core.contextmenu', 'plugin', mp)
                menu.popup(self, event)
                return
            self.on_context_menu(event)

    def on_motion(self, widget, *args):
        """
        Callback that responds to mouse motion in sequence view.

        @param event: Mouse event
        @type event: wx.MouseEvent
        """
        x, y, state = self.window.get_pointer()
        x = max(int(x), self.seq_left_margin)
        if self.dragging:
            select_track, select_row = self.pos_to_track_row((x, y))
            # start selection if nothing selected
            if self.selection_start == None:
                self.selection_start = (self.track, self.row)
            if self.selection_start:
                player = com.get('neil.core.player')
                seq = player.get_current_sequencer()
                select_track = min(seq.get_sequence_track_count() - 1,
                                   max(select_track, 0))
                select_row = max(select_row, 0)
                self.selection_end = (select_track, select_row)
                # If the user didn't drag enough to select more than one cell,
                # we reset.
                if (self.selection_start[0] == self.selection_end[0] and
                    self.selection_start[1] == self.selection_end[1]):
                    self.selection_start = None
                    self.selection_end = None
                self.redraw()

    def get_client_size(self):
        rect = self.get_allocation()
        return rect.width, rect.height

    def expose(self, widget, *args):
        #player = com.get('neil.core.player')
        if (self.needfocus):
            self.grab_focus()
            self.needfocus = False
        self.adjust_scrollbars()
        self.context = widget.window.new_gc()
        self.draw(self.context)
        self.panel.update_list()
        return False

    def redraw(self, *args):
        if self.get_window() is not None and self.window.is_visible():
            rect = self.get_allocation()
            self.window.invalidate_rect((0, 0, rect.width, rect.height), False)

    def on_left_up(self, widget, event):
        """
        Callback that responds to left click up in sequence view.

        @param event: Mouse event
        @type event: wx.MouseEvent
        """
        if event.button == 1:
            if self.dragging:
                self.dragging = False
                self.grab_remove()

    def update_position(self):
        """
        Updates the position.
        """
        #TODO: find a better way to find out whether we are visible
        #if self.rootwindow.get_current_panel() != self.panel:
        #       return True
        player = com.get('neil.core.player')
        playpos = player.get_position()
        if self.playpos != playpos:
            if self.panel.toolbar.followsong.get_active():
                if playpos >= self.get_endrow() or playpos < self.startseqtime:
                    self.startseqtime = playpos / self.step * self.step
                    self.redraw()
            #self.draw_cursors()
            self.draw_playpos()
            self.playpos = playpos
            self.draw_playpos()
            #self.redraw()
        return True

    def on_vscroll_window(self, widget, scroll, value):
        """
        Handles vertical window scrolling.
        """
        adj = widget.get_adjustment()
        minv = adj.get_property('lower')
        maxv = adj.get_property('upper')
        pagesize = adj.get_property('page-size')
        value = int(max(min(value, maxv - pagesize), minv) + 0.5)
        widget.set_value(value)
        self.redraw()
        if self.starttrack != value:
            self.starttrack = value
            self.redraw()
        return True

    def on_hscroll_window(self, widget, scroll, value):
        """
        Handles horizontal window scrolling.
        """
        adj = widget.get_adjustment()
        minv = adj.get_property('lower')
        maxv = adj.get_property('upper')
        pagesize = adj.get_property('page-size')
        value = int(max(min(value, maxv - pagesize), minv) + 0.5)
        widget.set_value(value)
        if self.startseqtime != value * self.step:
            self.startseqtime = value * self.step
            self.redraw()
        return True

    def adjust_scrollbars(self):
        w, h = self.get_client_size()
        vw, vh = self.get_virtual_size()
        pw, ph = (int((w - self.seq_left_margin) /
                     float(self.seq_row_size) + 0.5),
                  int((h - self.seq_top_margin) /
                      float(self.seq_track_size) + 0.5))
        #print w, h
        #print vw, vh
        #print pw, ph
        hrange = vw - pw
        vrange = vh - ph
        if hrange <= 0:
            self.hscroll.hide()
        else:
            self.hscroll.show()
        if vrange <= 0:
            self.vscroll.hide()
        else:
            self.vscroll.show()
        adj = self.hscroll.get_adjustment()
        adj.configure(self.startseqtime / self.step, 0,
                    int(vw + (w - self.seq_left_margin) /
                        float(self.seq_row_size) - 2),
                    1, 1, pw)
        adj = self.vscroll.get_adjustment()
        adj.configure(self.starttrack, 0, vh, 1, 1, ph)
        #self.redraw()

    def get_virtual_size(self):
        """
        Returns the size in characters of the virtual view area.
        """
        player = com.get('neil.core.player')
        seq = player.get_current_sequencer()
        tracklist = seq.get_track_list()
        total_length = 0
        for track_index in range(self.starttrack, len(tracklist)):
            track = tracklist[track_index]
            m = track.get_plugin()
            track_length = 0
            for pos, value in track.get_event_list():
                if value >= 0x10:
                    pat = m.get_pattern(value - 0x10)
                    length = pat.get_row_count()
                    pat.destroy()
                elif value == 0x00:
                    length = self.step
                elif value == 0x01:
                    length = self.step
                track_length += length
            if track_length > total_length:
                total_length = track_length
        h = seq.get_sequence_track_count()
        w = (max(self.row, player.get_song_end(), player.get_loop_end(), \
                total_length) / self.step + 3)
        return w, h

    def draw_cursors(self):
        """
        Overriding a Canvas method that is called after painting is completed.
        Draws an XOR play cursor over the pattern view.

        @param dc: wx device context.
        @type dc: wx.PaintDC
        """
        if not self.window:
            return
        player = com.get('neil.core.player')
        gc = self.window.new_gc()
        cr = self.window.cairo_create()
        colormap = gc.get_colormap()
        # drawable = self.window
        width, height = self.get_client_size()
        red = colormap.alloc_color('#ff0000')
        # white = colormap.alloc_color('#ffffff')
        gc.set_foreground(red)
        gc.set_background(red)
        gc.line_width = 2
        sequencer = player.get_current_sequencer()
        track_count = sequencer.get_sequence_track_count()
        if track_count > 0:
            if self.row >= self.startseqtime and self.track >= self.starttrack:
                if (self.selection_start != None and
                    self.selection_end != None):
                    start_track = min(self.selection_start[0],
                                      self.selection_end[0])
                    start_row = min(self.selection_start[1],
                                    self.selection_end[1])
                    end_track = max(self.selection_start[0],
                                    self.selection_end[0])
                    end_row = max(self.selection_start[1],
                                  self.selection_end[1])
                    x1, y1 = self.track_row_to_pos((start_track, start_row))
                    x2, y2 = self.track_row_to_pos((end_track + 1,
                                                    end_row + self.step))
                    cursor_x, cursor_y = x1, y1
                    cursor_width, cursor_height = x2 - x1, y2 - y1
                else:
                    cursor_x, cursor_y = self.track_row_to_pos((self.track,
                                                                self.row))
                    cursor_width = self.seq_row_size
                    cursor_height = self.seq_track_size
                cr.rectangle(cursor_x + 0.5, cursor_y + 0.5,
                             cursor_width, cursor_height)
                cr.set_source_rgba(1.0, 0.0, 0.0, 1.0)
                cr.set_line_width(1)
                cr.stroke_preserve()
                cr.set_source_rgba(1.0, 0.0, 0.0, 0.3)
                cr.fill()

    def draw_playpos(self):
        if not self.window:
            return
        # player = com.get('neil.core.player')
        gc = self.window.new_gc()
        colormap = gc.get_colormap()
        white = colormap.alloc_color('#ffffff')
        drawable = self.window
        width, height = self.get_client_size()
        if self.playpos >= self.startseqtime:
            gc.set_foreground(white)
            gc.set_background(white)
            gc.set_function(Gdk.XOR)
            x = self.seq_left_margin + int((float(self.playpos - self.startseqtime) / self.step) * self.seq_row_size) + 1
            drawable.draw_rectangle(gc, True, x, 1, 1, height - 1)

    def update(self):
        """
        Updates the view after a lot of data has changed. This will also
        reset selection.
        """
        self.startseqtime = self.startseqtime - (self.startseqtime % self.step)
        self.selection_start = None
        if self.row != -1:
            self.row = self.row - (self.row % self.step)
        self.redraw()

    def get_bounds(self):
        width, height = self.get_client_size()
        start = self.startseqtime
        width_in_bars = (width / self.seq_row_size) * self.step
        end = start + width_in_bars
        return (start, end)

    class memoize:
        def __init__(self, function):
            self.function = function
            self.memoized = {}

        def __call__(self, *args):
            try:
                return self.memoized[args]
            except KeyError:
                self.memoized[args] = self.function(*args)
                return self.memoized[args]

    @memoize
    def get_random_color(seed):
        """Generates a random color in html format."""
        random.seed(seed)
        r = int(random.random() * 105) + 150
        g = int(random.random() * 105) + 150
        b = int(random.random() * 105) + 150
        result = "#%2x%2x%2x" % (r, g, b)
        return result.replace(' ', '0')

    def draw_markers(self, ctx, colors):
        """
        Draw the vertical lines every few bars.
        """
        drawable = self.window
        width, height = self.get_client_size()
        x, y = self.seq_left_margin, self.seq_top_margin
        layout = Pango.Layout(self.get_pango_context())
        layout.set_width(-1)
        start = self.startseqtime
        while (x < width):
            if start % (4 * self.step) == 0:
                ctx.set_foreground(colors['Strong Line'])
                drawable.draw_line(ctx, x, 0, x, height)
                ctx.set_foreground(colors['Text'])
                layout.set_markup("<small>%s</small>" % str(start))
                px, py = layout.get_pixel_size()
                drawable.draw_layout(ctx, x + 2,
                                     self.seq_top_margin / 2 - py / 2, layout)
            else:
                ctx.set_foreground(colors['Weak Line'])
                drawable.draw_line(ctx, x, self.seq_top_margin, x, height)
            x += self.seq_row_size
            start += self.step
        ctx.set_foreground(colors['Border'])
        drawable.draw_line(ctx, 0, y, width, y)
        drawable.draw_line(ctx, self.seq_left_margin, 0,
                           self.seq_left_margin, height)
        ctx.set_foreground(colors['Track Background'])
        drawable.draw_rectangle(ctx, True, 0, 0,
                                self.seq_left_margin, height)

    def draw_tracks(self, ctx, colors):
        """
        Draw tracks and pattern boxes.
        """
        player = com.get('neil.core.player')
        drawable = self.window
        width, height = self.get_client_size()
        x, y = self.seq_left_margin, self.seq_top_margin
        layout = Pango.Layout(self.get_pango_context())
        layout.set_width(-1)
        layout.set_font_description(Pango.FontDescription("sans 8"))
        # cfg = config.get_config()
        sequencer = player.get_current_sequencer()
        tracks = sequencer.get_track_list()
        for track_index in range(self.starttrack, len(tracks)):
            track = tracks[track_index]
            plugin = track.get_plugin()
            plugin_info = self.plugin_info.get(plugin)
            # Draw the pattern boxes
            event_list = list(track.get_event_list())
            for (position, value), index in zip(event_list, list(range(len(event_list)))):
                pattern = None
                if value >= 0x10:
                    pattern = plugin.get_pattern(value - 0x10)
                    length = pattern.get_row_count()
                    end = position + length
                    width_in_bars = (width / self.seq_row_size) * self.step
                    if ((end >= self.startseqtime) and
                        (position < self.startseqtime + width_in_bars)):
                        try:
                            gfx = plugin_info.patterngfx[value]
                        except KeyError:
                            name = prepstr(pattern.get_name())
                            # Handle the case where the pattern overlaps with the next one.
                            # This is done by shortening the current pattern so they display nice.
                            try:
                                if position + length > event_list[index + 1][0]:
                                    length -= position + length - event_list[index + 1][0]
                            except IndexError:
                                pass
                            box_size = max(int(((self.seq_row_size * length) / self.step) + 0.5), 4)
                            gfx_w, gfx_h = box_size - 3, self.seq_track_size - 3
                            gfx = Gdk.Pixmap(drawable, gfx_w, gfx_h, -1)
                            pattern_color = self.get_random_color(plugin.get_name() + name)
                            ctx.set_foreground(ctx.get_colormap().alloc_color(pattern_color))
                            gfx.draw_rectangle(ctx, True, 0, 0, gfx_w, gfx_h)
                            if plugin.get_pluginloader().get_uri() == '@neil/lunar/controller/Control;1':
                                ctx.set_foreground(ctx.get_colormap().alloc_color('#404040'))
                                for row in range(length - 1):
                                    val1 = pattern.get_value(row, 1, 0, 0)
                                    val2 = pattern.get_value(row, 1, 0, 0)
                                    param = plugin.get_parameter(1, 0, 0)
                                    scale = 1.0 / (param.get_value_max() - param.get_value_min())
                                    if val1 != param.get_value_none() and val2 != param.get_value_none:
                                        scaled1 = (val1 - param.get_value_min()) * scale
                                        scaled2 = (val2 - param.get_value_min()) * scale
                                        gfx.draw_line(ctx,
                                                      int(1 + gfx_w * (row / float(length))),
                                                      int(1 + (gfx_h - 2) * (1.0 - scaled1)),
                                                      int(1 + gfx_w * ((row + 1) / float(length))),
                                                      int(1 + (gfx_h - 2) * (1.0 - scaled2)))
                            else:
                                ctx.set_foreground(ctx.get_colormap().alloc_color('#404040'))
                                for row in range(length):
                                    groups = pattern.get_group_count()
                                    for group in range(groups):
                                        tracks_ = pattern.get_track_count(group)
                                        for track in range(tracks_):
                                            cols = pattern.get_column_count(group, track)
                                            for col in range(cols):
                                                val = pattern.get_value(row, group, track, col)
                                                param = plugin.get_parameter(group, track, col)
                                                if param.get_type() in [0, 2, 3]:
                                                    if val != param.get_value_none():
                                                        scale = 1.0 / (param.get_value_max() - param.get_value_min())
                                                        scaled = (val - param.get_value_min()) * scale
                                                        gfx.draw_rectangle(ctx, True,
                                                                           int(1 + gfx_w * (row / float(length))),
                                                                           int(1 + (gfx_h - 2) * (1.0 - scaled)), 2, 2)
                            ctx.set_foreground(colors['Border'])
                            gfx.draw_rectangle(ctx, False, 0, 0, gfx_w - 1, gfx_h - 1)
                            layout.set_markup("<small>%s</small>" % name)
                            px, py = layout.get_pixel_size()
                            ctx.set_foreground(colors['Text'])
                            gfx.draw_layout(ctx, 2, 2, layout)
                            plugin_info.patterngfx[value] = gfx
                        x = self.seq_left_margin + ((position - self.startseqtime) * self.seq_row_size / self.step)
                        drawable.draw_drawable(ctx, gfx, 0, 0, x + 2, y + 2, -1, -1)
                    if pattern != None:
                        pattern.destroy()
                elif value == 0x00 or value == 0x01:
                    x = (self.seq_left_margin +
                         ((position - self.startseqtime) * self.seq_row_size) /
                         self.step)
                    if value == 0x00:
                        ctx.set_foreground(ctx.get_colormap().alloc_color('#ff0000'))
                    else:
                        ctx.set_foreground(ctx.get_colormap().alloc_color('#00ff00'))
                    ctx.line_width = 3
                    drawable.draw_line(ctx, x, y + 2, x, y + self.seq_track_size - 1)
                    ctx.line_width = 1
                else:
                    print("Weird pattern id value: ", value)
            # Draw the track name boxes.
            name = plugin.get_name()
            title = prepstr(name)
            if (player.solo_plugin and
                player.solo_plugin != plugin and
                is_generator(plugin)):
                title = "[%s]" % title
            elif self.plugin_info[plugin].muted or self.plugin_info[plugin].bypassed:
                title = "(%s)" % title
            # Draw a box that states the name of the machine on that track.
            if self.plugin_info[plugin].muted or self.plugin_info[plugin].bypassed:
                if (is_effect(plugin)):
                    ctx.set_foreground(colors['Effect Bg Mute'])
                elif (is_generator(plugin)):
                    ctx.set_foreground(colors['Generator Bg Mute'])
                elif (is_controller(plugin)):
                    ctx.set_foreground(colors['Controller Bg Mute'])
                elif (is_root(plugin)):
                    ctx.set_foreground(colors['Master Bg Mute'])
            else:
                if (is_effect(plugin)):
                    ctx.set_foreground(colors['Effect Bg'])
                elif (is_generator(plugin)):
                    ctx.set_foreground(colors['Generator Bg'])
                elif (is_controller(plugin)):
                    ctx.set_foreground(colors['Controller Bg'])
                elif (is_root(plugin)):
                    ctx.set_foreground(colors['Master Bg'])
            drawable.draw_rectangle(ctx, True, 0, y, self.seq_left_margin,
                                    self.seq_track_size)
            ctx.set_foreground(colors['Border'])
            drawable.draw_rectangle(ctx, False, 0, y, self.seq_left_margin,
                                    self.seq_track_size)
            ctx.set_foreground(colors['Border'])
            layout.set_markup("%s" % title)
            px, py = layout.get_pixel_size()
            # Draw the label with the track name
            drawable.draw_layout(ctx, self.seq_left_margin - 4 - px,
                                 y + self.seq_track_size / 2 - py / 2, layout)
            y += self.seq_track_size
            # Draw the horizontal lines separating tracks
            ctx.set_foreground(colors['Weak Line'])
            drawable.draw_line(ctx, self.seq_left_margin + 1, y, width - 1, y)
        cr = self.window.cairo_create()
        cr.rectangle(self.seq_left_margin, 0, 5, height)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.15)
        cr.fill()

    def draw_loop_points(self, ctx, colors):
        player = com.get('neil.core.player')
        drawable = self.window
        width, height = self.get_client_size()
        ctx.line_width = 1
        loop_start, loop_end = player.get_loop()
        window_start, window_end = self.get_bounds()
        if (loop_start >= window_start and loop_start <= window_end):
            # The right facing loop delimiter line with arrow.
            x, y = self.track_row_to_pos((0, loop_start))
            ctx.set_foreground(colors['Loop Line'])
            drawable.draw_line(ctx, x, 0, x, height)
            drawable.draw_polygon(ctx, filled=True,
                                  points=((x, 0), (x + 10, 0), (x, 10)))
        if (loop_end >= window_start and loop_end <= window_end):
            # The left facing loop delimiter with arrow.
            x, y = self.track_row_to_pos((0, loop_end))
            ctx.set_foreground(colors['Loop Line'])
            drawable.draw_line(ctx, x, 0, x, height)
            drawable.draw_polygon(ctx, filled=True,
                                  points=((x, 0), (x - 10, 0), (x, 10)))
        # Draw song end marker.
        ctx.line_width = 3
        song_end = player.get_song_end()
        if (song_end > window_start and song_end < window_end):
            x, y = self.track_row_to_pos((0, song_end))
            ctx.set_foreground(colors['End Marker'])
            drawable.draw_line(ctx, x, 0, x, height)
        ctx.line_width = 1

    def draw(self, ctx):
        """
        Overriding a L{Canvas} method that paints onto an offscreen buffer.
        Draws the pattern view graphics.
        """
        colormap = ctx.get_colormap()
        drawable = self.window
        width, height = self.get_client_size()
        cfg = config.get_config()
        colors = {
            'Background': colormap.alloc_color(cfg.get_color('SE Background')),
            'Border': colormap.alloc_color(cfg.get_color('SE Border')),
            'Strong Line': colormap.alloc_color(cfg.get_color('SE Strong Line')),
            'Weak Line': colormap.alloc_color(cfg.get_color('SE Weak Line')),
            'Text': colormap.alloc_color(cfg.get_color('SE Text')),
            'Track Background': colormap.alloc_color(cfg.get_color('SE Track Background')),
            'Track Foreground': colormap.alloc_color(cfg.get_color('SE Track Foreground')),
            'Loop Line': colormap.alloc_color(cfg.get_color('SE Loop Line')),
            'End Marker': colormap.alloc_color(cfg.get_color('SE End Marker')),
            'Master Bg': colormap.alloc_color(cfg.get_color('MV Master')),
            'Effect Bg': colormap.alloc_color(cfg.get_color('MV Effect')),
            'Generator Bg': colormap.alloc_color(cfg.get_color('MV Generator')),
            'Controller Bg': colormap.alloc_color(cfg.get_color('MV Controller')),
            'Master Bg Mute': colormap.alloc_color(cfg.get_color('MV Master Mute')),
            'Effect Bg Mute': colormap.alloc_color(cfg.get_color('MV Effect Mute')),
            'Generator Bg Mute': colormap.alloc_color(cfg.get_color('MV Generator Mute')),
            'Controller Bg Mute': colormap.alloc_color(cfg.get_color('MV Controller Mute'))
            }
        # Draw the background
        ctx.set_foreground(colors['Background'])
        drawable.draw_rectangle(ctx, True, 0, 0, width, height)
        self.draw_markers(ctx, colors)
        self.draw_tracks(ctx, colors)
        self.draw_loop_points(ctx, colors)
        self.draw_cursors()
        self.draw_playpos()
        # Draw the black border
        #ctx.set_foreground(colors['Border'])
        #drawable.draw_rectangle(ctx, False, 0, 0, width - 1, height - 1)

__all__ = [
'PatternNotFoundException',
'SequencerPanel',
'SequencerView',
]

__neil__ = dict(
    classes = [
        SequencerPanel,
        SequencerView,
    ],
)
