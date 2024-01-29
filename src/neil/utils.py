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
Provides utility functions needed all over the place,
which have no specific module or class they belong to.
"""

import time, sys, math, os, zzub, imp
from string import ascii_letters, digits
import struct
from gi.repository import GObject, Gtk, Gdk, GdkPixbuf
import weakref
import neil.com as com

def is_debug():
    if os.environ.get('NEIL_DEBUG'):
        return True
    return False

def is_win32():
    return sys.platform == 'win32'

def is_frozen():
    """
    Determines whether the application is being executed by
    a Python installation or it is running standalone (as a
    py2exe executable.)

    @return: True if frozen, otherwise False
    @rtype: bool
    """
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") # old py2exe
        or imp.is_frozen("__main__")) # tools/freeze

def get_root_folder_path():
    """
    Returns the base folder from which this script is being
    executed. This is mainly used for windows, where loading
    of resources relative to the execution folder must be
    possible, regardless of current working directory.

    @return: Path to execution folder.
    @rtype: str
    """
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__))))

basedir = get_root_folder_path()

def etcpath(path):
    """
    Translates a path relative to the config directory into an absolute
    path.

    @param path: Relative path to file.
    @type path: str
    @return: Absolute path to file.
    @rtype: str
    """
    from .pathconfig import path_cfg
    return path_cfg.get_path('etc', path)

def iconpath(path):
    """
    Translates a path relative to the neil icon directory into an absolute
    path.

    @param path: Relative path to file.
    @type path: str
    @return: Absolute path to file.
    @rtype: str
    """
    from .pathconfig import path_cfg
    return path_cfg.get_path('icons_neil', path)

def hicoloriconpath(path):
    """
    Translates a path relative to the hicolor icon directory into an absolute
    path.

    @param path: Relative path to file.
    @type path: str
    @return: Absolute path to file.
    @rtype: str
    """
    from .pathconfig import path_cfg
    return path_cfg.get_path('icons_hicolor', path)


def imagepath(path):
    """
    Translates a path relative to the image directory into an absolute
    path.

    @param path: Relative path to file.
    @type path: str
    @return: Absolute path to file.
    @rtype: str
    """
    from .pathconfig import path_cfg
    return path_cfg.get_path('pixmaps', path)

def sharedpath(path):
    """
    Translates a path relative to the shared directory into an absolute
    path.

    @param path: Relative path to file.
    @type path: str
    @return: Absolute path to file.
    @rtype: str
    """
    from .pathconfig import path_cfg
    return path_cfg.get_path('share', path)

def docpath(path):
    """
    Translates a path relative to the doc directory in to an absolute
    path.
    """
    from .pathconfig import path_cfg
    return path_cfg.get_path('doc', path)

def filepath(path):
    """
    Translates a path relative to a base dir into an absolute
    path.
    WIN32: If the path leads to an svg and there is a similar file with
    png extension, use that one instead.

    @param path: Relative path to file.
    @type path: str
    @return: Absolute path to file.
    @rtype: str
    """
    path = os.path.abspath(os.path.normpath(os.path.join(basedir,path)))
    if is_win32() and path.lower().endswith('.svg'):
        pngpath = os.path.splitext(path)[0] + '.png'
        if os.path.isfile(pngpath):
            return pngpath
    return path

def cmp(a, b):
    return (a > b) - (a < b) 

def db2linear(val, limit = -48.0):
    """
    Translates a dB volume to a linear amplitude.

    @param val: Volume in dB.
    @type val: float
    @param limit: If val is lower than limit, 0.0 will be returned.
    @type limit: float
    @return: Linear amplitude.
    @rtype: float
    """
    if val == 0.0:
        return 1.0
    if val <= limit:
        return 0.0
    return 10 ** (val / 20.0)

def linear2db(val, limit = -48.0):
    """
    Translates a linear amplitude to a dB volume.

    @param val: Linear amplitude between 0.0 and 1.0.
    @type val: float
    @param limit: If amplitude is zero or lower, limit will be returned.
    @type limit: float
    @return: Volume in dB.
    @rtype: float
    """
    if val <= 0.0:
        return limit
    return math.log(val) * 20.0 / math.log(10)

def format_time(t):
    """
    Translates a time value into a string of the format
    "h:mm:ss:ms".

    @param t: Relative time value.
    @type t: float
    @return: String of the format "h:mm:ss:ms".
    @rtype: str
    """
    h = int(t / 3600)
    m = int((t % 3600) / 60)
    s = t % 60
    ms = int((t - int(t))*10.0)
    return "%i:%02i:%02i:%i" % (h,m,s,ms)

def ticks_to_time(ticks,bpm,tpb):
    """
    Translates positions in ticks as returned by zzub
    to time values.

    @param ticks: Tick value as returned by zzub.
    @type ticks: int
    @param bpm: Beats per minutes.
    @type bpm: int
    @param tpb: Ticks per beats.
    @type tpb: int
    @return: Relative time value.
    @rtype: float
    """
    return (float(ticks)*60) / (bpm * tpb)

def prepstr(s, fix_underscore=False):
    """
    prepstr ensures that a string is always
    ready to be displayed in a GUI control by wxWidgets.

    @param s: Text to be prepared.
    @type s: str
    @return: Correctly encoded text.
    @rtype: str
    """
    s = s.decode('latin-1')
    if fix_underscore:
        s = s.replace('_','__')
    return s

def fixbn(v):
    """
    Occasionally, invalid note inputs are being made,
    either by user error or invalid paste or loading operations.
    This function fixes a Buzz note value so it has
    always a correct value.

    @param v: Buzz note value.
    @type v: int
    @return: Corrected Buzz note value.
    @rtype: int
    """
    if v == zzub.zzub_note_value_off:
        return v
    o,n = ((v & 0xf0) >> 4), (v & 0xf)
    o = min(max(o,0),9)
    n = min(max(n,1),12)
    return (o << 4) | n

def bn2mn(v):
    """
    Converts a Buzz note value into a MIDI note value.

    @param v: Buzz note value.
    @type v: int
    @return: MIDI note value.
    @rtype: int
    """
    if v == zzub.zzub_note_value_off:
        return 255
    return ((v & 0xf0) >> 4)*12 + (v & 0xf)-1

def mn2bn(v):
    """
    Converts a MIDI note value into a Buzz note value.

    @param v: MIDI note value.
    @type v: int
    @return: Buzz note value.
    @rtype: int
    """
    if v == 255:
        return zzub.zzub_note_value_off
    return ((int(v)/12) << 4) | ((v%12)+1)

NOTES = ('?-','C-','C#','D-','D#','E-','F-','F#','G-','G#','A-','A#','B-')

def note2str(p,v):
    """
    Translates a Buzz note value into a string of the format
    "NNO", where NN is note, and O is octave.

    @param p: A parameter object. You can supply None here
    if the value is not associated with a plugin parameter.
    @type p: zzub.Parameter
    @return: A string of the format "NNO", where NN is note,
    and O is octave, or "..." for no value.
    @rtype: str
    """
    if p and (v == p.get_value_none()):
        return '...'
    if v == zzub.zzub_note_value_off:
        return 'off'
    o,n = (v & 0xf0) >> 4, v & 0xf
    return "%s%i" % (NOTES[n],o)

def switch2str(p,v):
    """
    Translates a Buzz switch value into a hexstring ready to
    be printed in a pattern view.

    @param p: A plugin parameter object.
    @type p: zzub.Parameter
    @param v: A Buzz switch value.
    @type v: int
    @return: A 1-digit hexstring or "." for no value.
    @rtype: str
    """
    if v == p.get_value_none():
        return '.'
    return "%1X" % v

def byte2str(p,v):
    """
    Translates a Buzz byte value into a hexstring ready to
    be printed in a pattern view.

    @param p: A plugin parameter object.
    @type p: zzub.Parameter
    @param v: A Buzz byte value.
    @type v: int
    @return: A 2-digit hexstring or ".." for no value.
    @rtype: str
    """
    if v == p.get_value_none():
        return '..'
    return "%02X" % v

def word2str(p,v):
    """
    Translates a Buzz word value into a hexstring ready to
    be printed in a pattern view.

    @param p: A plugin parameter object.
    @type p: zzub.Parameter
    @param v: A Buzz word value.
    @type v: int
    @return: A 4-digit hexstring or "...." for no value.
    @rtype: str
    """
    if v == p.get_value_none():
        return '....'
    return "%04X" % v

def roundint(v):
    """
    Rounds a float value to the next integer if its
    fractional part is larger than 0.5.

    @type v: float
    @rtype: int
    """
    return int(v+0.5)

def buffersize_to_latency(bs, sr):
    """
    Translates buffer size to latency.

    @param bs: Size of buffer in samples.
    @type bs: int
    @param sr: Samples per second in Hz.
    @type sr: int
    @return: Latency in ms.
    @rtype: float
    """
    return (float(bs) / float(sr)) * 1000.0

def filenameify(text):
    """
    Replaces characters in a text in such a way
    that it's feasible to use it as a filename. The
    result will be lowercase and all special chars
    replaced by underscores.

    @param text: The original text.
    @type text: str
    @return: The filename.
    @rtype: str
    """
    return ''.join([(c in (ascii_letters+digits) and c) or '_' for c in text.lower()])

def read_int(f):
    """
    Reads an 32bit integer from a binary file.
    """
    return struct.unpack('<I', f.read(4))[0]

def read_string(f):
    """
    Reads a pascal string (32bit len, data) from a binary file.
    """
    size = read_int(f)
    return f.read(size)

def write_int(f,v):
    """
    Writes a 32bit integer to a binary file.
    """
    f.write(struct.pack('<I', v))

def write_string(f,s):
    """
    Writes a pascal string (32bit len, data) to a binary file.
    """
    s = str(s)
    write_int(f, len(s))
    f.write(s)

def blend (color1, color2, weight = 0.5):
    """
        Blend (lerp) two Gdk.Colors
    """
    return Gdk.Color (
        color1.red_float   * weight + color2.red_float   * (1 - weight),
        color1.green_float * weight + color2.green_float * (1 - weight),
        color1.blue_float  * weight + color2.blue_float  * (1 - weight))

def from_hsb(h=0.0,s=1.0,b=1.0):
    """
    Converts hue/saturation/brightness into red/green/blue components.
    """
    if not s:
        return b,b,b
    scaledhue = (h%1.0)*6.0
    index = int(scaledhue)
    fraction = scaledhue - index
    p = b * (1.0 - s)
    q = b * (1.0 - s*fraction)
    t = b * (1.0 - s*(1.0 - fraction))
    if index == 0:
        return b,t,p
    elif index == 1:
        return q,b,p
    elif index == 2:
        return p,b,t
    elif index == 3:
        return p,q,b
    elif index == 4:
        return t,p,b
    elif index == 5:
        return b,p,q
    return b,p,q

def to_hsb(r,g,b):
    """
    Converts red/green/blue into hue/saturation/brightness components.
    """
    if (r == g) and (g == b):
        h = 0.0
        s = 0.0
        b = r
    else:
        v = float(max(r,g,b))
        temp = float(min(r,g,b))
        diff = v - temp
        if v == r:
            h = (g - b)/diff
        elif v == g:
            h = (b - r)/diff + 2
        else:
            h = (r - g)/diff + 4
        if h < 0:
            h += 6
        h = h / 6.0
        s = diff / v
        b = v
    return h,s,b

def run_function_with_progress(parent, msg, allow_cancel, func, *args):
    """
    Shows a progress dialog.
    """
    buttons = []
    if allow_cancel:
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    else:
        buttons = None
    dialog = Gtk.Dialog(
        '',
        parent and parent.get_toplevel(),
        Gtk.DialogFlags.DESTROY_WITH_PARENT,
        buttons)
    label = Gtk.Label()
    label.set_markup(msg)
    label.set_alignment(0,0.5)
    progress = Gtk.ProgressBar()
    vbox = Gtk.VBox(False, 6)
    vbox.set_border_width(6)
    vbox.pack_start(label)
    vbox.pack_start(progress)
    dialog._label = label
    dialog._progress = progress
    dialog.markup = msg
    dialog._response = None
    dialog.fraction = 0.0
    dialog.vbox.add(vbox)
    dialog.show_all()
    def update_progress(dlg):
        dlg._progress.set_fraction(dlg.fraction)
        dlg._label.set_markup(dlg.markup)
        time.sleep(0.01)
        return True
    def on_response(dialog, response):
        dialog._response = response
    dialog.connect('response', on_response)
    def run_function(dlg, func, args):
        if func(dlg, *args) and dlg._response == None:
            dlg.response(Gtk.ResponseType.OK)
    GObject.timeout_add(50, update_progress, dialog)
    import _thread
    _thread.start_new_thread(run_function, (dialog,func,args))
    response = dialog.run()
    dialog.destroy()
    return response

def gettext(parent, msg, text=''):
    """
    Shows a dialog to get some text.
    """
    dialog = Gtk.Dialog(
        '',
        parent and parent.get_toplevel(),
        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        (Gtk.STOCK_OK, True, Gtk.STOCK_CANCEL, False))
    label = Gtk.Label()
    label.set_markup(msg)
    label.set_alignment(0, 0.5)
    entry = Gtk.Entry()
    entry.set_text(text)
    entry.connect('activate', lambda widget: dialog.response(True))
    vbox = Gtk.VBox(False, 6)
    vbox.set_border_width(6)
    vbox.pack_start(label)
    vbox.pack_end(entry, expand=False)
    dialog.vbox.add(vbox)
    dialog.show_all()
    response = dialog.run()
    text = entry.get_text()
    dialog.destroy()
    if response:
        return text

def question(parent, msg, allowcancel = True):
    """
    Shows a question dialog.
    """
    dialog = Gtk.MessageDialog(parent.get_toplevel(),
                   Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                   Gtk.MESSAGE_QUESTION , Gtk.ButtonsType.NONE)
    dialog.set_markup(msg)
    dialog.add_buttons(
        Gtk.STOCK_YES, Gtk.ResponseType.YES,
        Gtk.STOCK_NO, Gtk.ResponseType.NO)
    if allowcancel:
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    response = dialog.run()
    dialog.destroy()
    return response

def error(parent, msg, msg2=None, details=None):
    """
    Shows an error message dialog.
    """
    dialog = Gtk.MessageDialog(parent and parent.get_toplevel(),
                   Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                   Gtk.MessageType.ERROR , Gtk.ButtonsType.NONE)
    dialog.set_markup(msg)
    dialog.set_resizable(True)
    if msg2:
        dialog.format_secondary_text(msg2)
    if details:
        expander = Gtk.Expander("Details")
        dialog.vbox.pack_start(expander, False, False, 0)
        label = Gtk.TextView()
        label.set_editable(False)
        label.get_buffer().set_property('text', details)
        label.set_wrap_mode(Gtk.WrapMode.NONE)

        sw = Gtk.ScrolledWindow()
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        sw.add(label)
        expander.add(sw)
        dialog.show_all()
    dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response

def message(parent, msg):
    """
    Shows an info message dialog.
    """
    dialog = Gtk.MessageDialog(parent.get_toplevel(),
                   Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                   Gtk.MESSAGE_INFO , Gtk.ButtonsType.NONE)
    dialog.set_markup(msg)
    dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response

def warning(parent, msg):
    """
    Shows an warning message dialog.
    """
    dialog = Gtk.MessageDialog(parent.get_toplevel(),
                   Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                   Gtk.MESSAGE_WARNING, Gtk.ButtonsType.NONE)
    dialog.set_markup(msg)
    dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response

def new_listview(columns):
    """
    Creates a list store with multiple columns.
    """
    treeview = Gtk.TreeView()
    treeview.set_rules_hint(True)
    store, columncontrols = new_liststore(treeview, columns)
    return treeview,store,columncontrols

def new_combobox(columns):
    """
    Creates a combobox.
    """
    combobox = Gtk.ComboBox()
    store, columncontrols = new_liststore(combobox, columns)
    return combobox

def new_liststore(view, columns):
    """
    Creates a Gtk.TreeView for a list store with multiple columns.
    """
    class ToggledHandler:
        def fixed_toggled(self, cell, path, model):
            iter = model.get_iter((int(path),))
            checked = model.get_value(iter, self.column)
            checked = not checked
            model.set(iter, self.column, checked)

    liststore = Gtk.ListStore(*[col[1] for col in columns])
    view.set_model(liststore)
    columncontrols = []
    for i,args in enumerate(columns):
        assert len(args) >= 2
        options = {}
        if len(args) == 2:
            name,coltype = args
        else:
            name,coltype,options = args
        if name == None:
            continue
        if isinstance(view, Gtk.ComboBox):
            if i > 0:
                break
            column = view
        else:
            column = Gtk.TreeViewColumn(name)
        if coltype == str:
            if isinstance(column, Gtk.TreeViewColumn):
                column.set_resizable(True)
            if options.get('icon',False):
                cellrenderer = Gtk.CellRendererPixbuf()
                column.pack_start(cellrenderer)
                column.add_attribute(cellrenderer, 'icon-name', i)
            else:
                cellrenderer = Gtk.CellRendererText()
                column.pack_start(cellrenderer, expand=False)
                if options.get('markup',False):
                    column.add_attribute(cellrenderer, 'markup', i)
                else:
                    column.add_attribute(cellrenderer, 'text', i)
                if options.get('wrap',False):
                    cellrenderer.set_property('wrap-width', options.get('width', 250))
        elif coltype == bool:
            th = ToggledHandler()
            th.column = i
            cellrenderer = Gtk.CellRendererToggle()
            cellrenderer.connect('toggled', th.fixed_toggled, liststore)
            column.pack_start(cellrenderer)
            column.add_attribute(cellrenderer, 'active', i)
        elif coltype == GdkPixbuf:
            cellrenderer = Gtk.CellRendererPixbuf()
            column.pack_start(cellrenderer)
            column.add_attribute(cellrenderer, 'pixbuf', i)
        if isinstance(view, Gtk.TreeView):
            view.append_column(column)
            column.set_sort_column_id(i)
        columncontrols.append(column)
    if isinstance(view, Gtk.TreeView):
        view.set_search_column(0)
    return liststore, columncontrols

def new_image_button(path, tooltip, width=20, height=20):
    """
    Creates a button with a single image.
    """
    image = Gtk.Image()
    image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(path, width, height))
    button = Gtk.Button()
    button.set_tooltip_text(tooltip)
    button.set_image(image)
    return button

def new_stock_image_button(stockid, tooltip=None):
    """
    Creates a button with a stock image.
    """
    image = Gtk.Image()
    image.set_from_stock(stockid, Gtk.IconSize.BUTTON)
    button = Gtk.Button()
    button.set_image(image)
    if tooltip is not None:
        button.set_tooltip_text(tooltip)
    return button

def new_stock_image_toggle_button(stockid, tooltip=None, tooltips_object=None):
    """
    Creates a toggle button with a stock image.
    """
    image = Gtk.Image()
    image.set_from_stock(stockid, Gtk.IconSize.BUTTON)
    button = Gtk.ToggleButton()
    button.set_image(image)
    if tooltips_object:
        tooltips_object.set_tip(button, tooltip)
    elif tooltip:
        button.set_tooltip_text(tooltip)
    return button

def new_image_toggle_button(path, tooltip=None, width=20, height=20):
    """
    Creates a toggle button with a single image.
    """
    image = Gtk.Image()
    image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(path, width, height))
    button = Gtk.ToggleButton()
    if tooltip:
        button.set_tooltip_text(tooltip)
    button.set_image(image)
    return button

def new_theme_image(name,size):
    theme = Gtk.icon_theme_get_default()
    image = Gtk.Image()
    if theme.has_icon(name):
        pixbuf = theme.load_icon(name, size, 0)
        image.set_from_pixbuf(pixbuf)
    return image

def new_theme_image_toggle_button(name, tooltip=None, tooltips_object=None):
    """
    Creates a toggle button with a default icon theme image.
    """
    image = new_theme_image(name,Gtk.IconSize.BUTTON)
    button = Gtk.ToggleButton()
    if tooltips_object:
        tooltips_object.set_tip(button, tooltip)
    elif tooltip:
        button.set_tooltip_text(tooltip)
    button.set_image(image)
    return button

def get_item_count(model):
    """
    Returns the number of items contained in a tree model.
    """
    class Count:
        value = 0
    def inc_count(model, path, iter, data):
        data.value += 1
    count = Count()
    model.foreach(inc_count,count)
    return count.value

def add_scrollbars(view):
    """
    adds scrollbars around a view
    """
    scrollwin = Gtk.ScrolledWindow()
    scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    if isinstance(view, Gtk.TreeView):
        scrollwin.set_shadow_type(Gtk.ShadowType.IN)
        scrollwin.add(view)
    else:
        scrollwin.add_with_viewport(view)
    return scrollwin

def add_vscrollbar(view):
    """
    adds a vertical scrollbar to a view
    """
    scrollwin = Gtk.ScrolledWindow()
    scrollwin.set_policy(Gtk.POLICY_NEVER, Gtk.PolicyType.AUTOMATIC)
    if isinstance(view, Gtk.TreeView):
        scrollwin.set_shadow_type(Gtk.ShadowType.IN)
        scrollwin.add(view)
    else:
        scrollwin.add_with_viewport(view)
    return scrollwin

def add_hscrollbar(view):
    """
    adds a vertical scrollbar to a view
    """
    scrollwin = Gtk.ScrolledWindow()
    scrollwin.set_policy(Gtk.POLICY_ALWAYS, Gtk.POLICY_NEVER)
    if isinstance(view, Gtk.TreeView):
        scrollwin.set_shadow_type(Gtk.ShadowType.IN)
        scrollwin.add(view)
    else:
        scrollwin.add_with_viewport(view)
    return scrollwin

def file_filter(name,*patterns):
    ff = Gtk.FileFilter()
    ff.set_name(name)
    for pattern in patterns:
        ff.add_pattern(pattern.upper())
        ff.add_pattern(pattern.lower())
    return ff


def format_filesize(size):
    if (size / (1<<40)):
        return "%.2f TB" % (float(size) / (1<<40))
    elif (size / (1<<30)):
        return "%.2f GB" % (float(size) / (1<<30))
    elif (size / (1<<20)):
        return "%.2f MB" % (float(size) / (1<<20))
    elif (size / (1<<10)):
        return "%.2f KB" % (float(size) / (1<<10))
    else:
        return "%i bytes" % size

def set_clipboard_text(data):
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(data, len(data))
    clipboard.store()

def get_clipboard_text():
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    return clipboard.wait_for_text()

def diff(oldlist, newlist):
    """
    Compares two lists and returns a list of elements that were
    added, and a list of elements that were removed.
    """
    return [x for x in newlist if x not in oldlist],[x for x in oldlist if x not in newlist] # add, remove

def wave_names_generator():
    player = com.get('neil.core.player')
    for i in range(player.get_wave_count()):
        w = player.get_wave(i)
        name = "%02X. %s" % ((i + 1), prepstr(w.get_name()))
        yield name

from itertools import islice, chain, repeat

def partition(iterable, part_len):
    """
    Partitions a list into specified slices
    """
    itr = iter(iterable)
    while 1:
        item = tuple(islice(itr, part_len))
        if len(item) < part_len:
            raise StopIteration
        yield item

def padded_partition(iterable, part_len, pad_val=None):
    """
    Partitions a list, with optional padding character support.
    """
    padding = repeat(pad_val, part_len-1)
    itr = chain(iter(iterable), padding)
    return partition(itr, part_len)


PLUGIN_FLAGS_MASK = zzub.zzub_plugin_flag_is_root|zzub.zzub_plugin_flag_has_audio_input|zzub.zzub_plugin_flag_has_audio_output|zzub.zzub_plugin_flag_has_event_output
ROOT_PLUGIN_FLAGS = zzub.zzub_plugin_flag_is_root|zzub.zzub_plugin_flag_has_audio_input|zzub.zzub_plugin_flag_has_audio_output
GENERATOR_PLUGIN_FLAGS = zzub.zzub_plugin_flag_has_audio_output
EFFECT_PLUGIN_FLAGS = zzub.zzub_plugin_flag_has_audio_input|zzub.zzub_plugin_flag_has_audio_output
CONTROLLER_PLUGIN_FLAGS = zzub.zzub_plugin_flag_has_event_output

def is_effect(plugin):
    return ((plugin.get_flags() & PLUGIN_FLAGS_MASK) == EFFECT_PLUGIN_FLAGS)

def is_generator(plugin):
    return ((plugin.get_flags() & PLUGIN_FLAGS_MASK) == GENERATOR_PLUGIN_FLAGS)

def is_controller(plugin):
    return ((plugin.get_flags() & PLUGIN_FLAGS_MASK) == CONTROLLER_PLUGIN_FLAGS)

def is_root(plugin):
    return ((plugin.get_flags() & PLUGIN_FLAGS_MASK) == ROOT_PLUGIN_FLAGS)

def is_streamer(plugin):
    return (plugin.get_flags() & zzub.zzub_plugin_flag_stream)

def get_new_pattern_name(plugin):
    """
    Finds an unused pattern name.
    """
    patternid = 0
    while True:
        s = "%02i" % patternid
        found = False
        for p in plugin.get_pattern_list():
            if p.get_name() == s:
                found = True
                patternid += 1
                break
        if not found:
            break
    return s

class CancelException(Exception):
    """
    Is being thrown when the user hits cancel in a sequence of
    modal UI dialogs.
    """

def make_submenu_item(submenu, name):
    item = Gtk.MenuItem(label=name)
    item.set_submenu(submenu)
    return item

def make_stock_menu_item(stockid, func, frame=None, shortcut=None, *args):
    item = Gtk.ImageMenuItem(stockid)
    if frame and shortcut:
        acc = com.get('neil.core.accelerators')
        acc.add_accelerator(shortcut, item)
    if func:
        item.connect('activate', func, *args)
    return item

def make_stock_tool_item(stockid, func, *args):
    item = Gtk.ToolButton(stockid)
    if func:
        item.connect('clicked', func, *args)
    return item

def make_stock_toggle_item(stockid, func, *args):
    item = Gtk.ToggleToolButton(stockid)
    if func:
        item.connect('toggled', func, *args)
    return item

def make_stock_radio_item(stockid, func, *args):
    item = Gtk.RadioToolButton(stock_id=stockid)
    if func:
        item.connect('toggled', func, *args)
    return item

def make_menu_item(label, desc, func, *args):
    item = Gtk.MenuItem(label=label)
    if desc:
        item.set_tooltip_text(desc)
    if func:
        item.connect('activate', func, *args)
    return item

def make_check_item(label, desc, func, *args):
    item = Gtk.CheckMenuItem(label=label)
    if desc:
        item.set_tooltip_text(desc)
    if func:
        item.connect('toggled', func, *args)
    return item

def make_radio_item(label, desc, func, *args):
    item = Gtk.RadioMenuItem(label=label)
    if desc:
        item.set_tooltip_text(desc)
    if func:
        item.connect('toggled', func, *args)
    return item

def camelcase_to_unixstyle(s):
    o = ''
    for c in s:
        if c.isupper() and o and not o.endswith('_'):
            o += '_'
        o += c.lower()
    return o

def test_view(classname):
    obj = com.get(classname)
    if isinstance(obj, Gtk.Window):
        pass
    elif isinstance(obj, Gtk.Dialog):
        pass
    elif isinstance(obj, Gtk.Widget) and not obj.get_parent():
        dlg = com.get('neil.test.dialog', embed=obj, destroy_on_close=False)

def show_manual():
    """
    Invoke yelp program with the Neil manual.
    """
    import webbrowser
    path = docpath("manual")
    webbrowser.open_new("%s/index.html" % path)

def show_machine_manual(name):
    """
    Invoke yelp program to display the manual of a specific machine.
    Parameter name is the long name of the machine in all lower caps
    and with spaces replaced by underscores.
    """
    import webbrowser
    path = docpath("manual")
    if os.path.isfile((path + "/%s.html") % name):
        webbrowser.open_new("%s/%s.html" % (path, name))
        return True
    else:
        return False

class ObjectHandlerGroup:
    """
    allows to block/unblock a bank of handlers
    """

    class Unblocker:
        def __init__(self, ohg):
            self.ohg = ohg
        def __del__(self):
            self.ohg.unblock()

    def __init__(self):
        self.handlers = []

    def connect(self, widget, eventname, *args):
        handler = widget.connect(eventname, *args)
        self.handlers.append((widget,handler))

    def autoblock(self):
        """
        autoblock will return a token which calls
        unblock() when going out of scope. you must
        not store the token permanently.
        """
        self.block()
        return self.Unblocker(self)

    def block(self):
        for widget,handler in self.handlers:
            widget.handler_block(handler)

    def unblock(self):
        for widget,handler in self.handlers:
            widget.handler_unblock(handler)

class Menu(Gtk.Menu):
    def add_separator(self):
        self.append(Gtk.SeparatorMenuItem())

    def add_submenu(self, label, submenu = None):
        if not submenu:
            submenu = Menu()
        item = Gtk.MenuItem(label=label)
        item.set_submenu(submenu)
        self.append(item)
        return item, submenu

    def add_item(self, label, func, *args):
        item = Gtk.MenuItem(label=label)
        item.connect('activate', func, *args)
        self.append(item)
        return item

    def add_item_no_underline(self, label, func, *args):
        item = Gtk.MenuItem(label=label, use_underline=False)
        item.connect('activate', func, *args)
        self.append(item)
        return item

    def add_check_item(self, label, toggled, func, *args):
        item = Gtk.CheckMenuItem(label=label)
        item.set_active(toggled)
        item.connect('toggled', func, *args)
        self.append(item)
        return item

    def add_image_item(self, label, icon_or_path, func, *args):
        item = Gtk.ImageMenuItem(stock_id=label)
        if isinstance(icon_or_path, str):
            image = Gtk.Image()
            image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(icon_or_path))
        elif isinstance(icon_or_path, Gtk.Image):
            image = icon_or_path
        item.set_image(image)
        item.connect('activate', func, *args)
        self.append(item)
        return item

    def popup(self, parent, event=None):
        self.show_all()
        if not self.get_attach_widget():
            self.attach_to_widget(parent and parent.get_toplevel(), None)
        if event:
            event_button = event.button
            event_time = event.time
        else:
            event_button = 0
            event_time = 0
        Gtk.Menu.popup(self, None, None, None, event_button, event_time)

class PropertyEventHandler:
    def get_eventbus(self):
        return com.get('neil.core.eventbus')

    def getter(self, membername, kwargs):
        value = getattr(self, '__' + membername)
        onget = kwargs.get('onget',None)
        if onget:
            value = onget(value)
        return value

    def setter(self, membername, kwargs, value):
        onset = kwargs.get('onset',None)
        if onset:
            value = onset(value)
        setattr(self, '__' + membername, value)
        eventname = kwargs.get('event', membername + '_changed')
        eventbus = self.get_eventbus()
        getattr(eventbus, eventname)(value)

    def listgetter(self, membername, kwargs):
        value = getattr(self, '__' + membername)
        onget = kwargs.get('onget',None)
        if onget:
            value = onget(value)
        return value[:]

    def listsetter(self, membername, kwargs, values):
        onset = kwargs.get('onset',None)
        if onset:
            values = onset(values)
        setattr(self, '__' + membername, values)
        eventname = kwargs.get('event', membername + '_changed')
        eventbus = self.get_eventbus()
        getattr(eventbus, eventname)(values[:])

def generate_ui_method(class_, membername, kwargs):
    doc = kwargs.get('doc', '')

    onset = kwargs.get('onset', None)
    onget = kwargs.get('onget', None)

    if kwargs.get('list', False):
        vtype = kwargs['vtype']
        getter = lambda self: self.listgetter(membername,kwargs)
        setter = lambda self,value: self.listsetter(membername,kwargs,value)
        default = kwargs.get('default', [])
    else:
        if 'default' in kwargs:
            default = kwargs['default']
            vtype = kwargs.get('vtype', type(default))
        else:
            vtype = kwargs['vtype']
            default = {float: 0.0, int:0, int:0, str:'', str:'', bool:False}.get(vtype, None)
        getter = lambda self,defvalue=kwargs.get(default,False): self.getter(membername,kwargs)
        setter = lambda self,value: self.setter(membername,kwargs,value)

    setattr(class_, '__' + membername, default)

    getter.__name__ = 'get_' + membername
    getter.__doc__ = 'Returns ' + doc
    setattr(class_, 'get_' + membername, getter)

    setter.__name__ = 'set_' + membername
    setter.__doc__ = 'Sets ' + doc
    setattr(class_, 'set_' + membername, setter)

    # add a property
    prop = property(getter, setter, doc=doc)
    setattr(class_, membername, prop)

def generate_ui_methods(class_, memberlist):
    # build getters and setters based on the options map
    for membername,kwargs in memberlist.items():
        generate_ui_method(class_, membername, kwargs)

def refresh_gui():
    while Gtk.events_pending():
        Gtk.main_iteration_do(block=False)

def synchronize_list(old_list, new_list, insert_entry_func=None, del_entry_func=None, swap_entry_func=None):
    """
    synchronizes a list with another using the smallest number of operations required.
    both lists need to contain only unique elements, that is: no list may contain the same element twice.

    if no functions are supplied for insert, del and swap operations, all operations will be directly
    performed on old_list.
    """
    def insert_entry(i,o):
        old_list.insert(i,o)
    def del_entry(i):
        del old_list[i]
    def swap_entry(i,j):
        a = old_list[i]
        b = old_list[j]
        del_entry_func(j)
        del_entry_func(i)
        insert_entry_func(i,b)
        insert_entry_func(j,a)
    if not insert_entry_func:
        insert_entry_func = insert_entry
    if not del_entry_func:
        del_entry_func = del_entry
    if not swap_entry_func:
        swap_entry_func = swap_entry
    original_list = list(old_list) # make a copy we synchronize changes with
    # remove all indices that are gone, in reverse order so
    # we don't shift indices around
    for index,item in reversed(list(enumerate(original_list))):
        if not item in new_list:
            del original_list[index]
            del_entry_func(index)
    # insert all new items from first to last, so indices
    # shift properly to fit.
    for index,item in enumerate(new_list):
        if not item in original_list:
            original_list.insert(index, item)
            insert_entry_func(index, item)
    # now both lists are in sync, but wrongly sorted
    assert len(original_list) == len(new_list)
    for i,item in enumerate(original_list):
        if new_list[i] == item:
            continue # already in the right place
        # find the new location
        j = new_list.index(item)
        # move entry
        if (i > j):
            i,j = j,i
        a = original_list[i]
        b = original_list[j]
        del original_list[j]
        del original_list[i]
        original_list.insert(i,b)
        original_list.insert(j,a)
        swap_entry_func(i,j)

class AcceleratorMap:
    def __init__(self):
        self.__keymap = {}

    def add_accelerator(self, shortcut, func, *args, **kargs):
        # cleanup string by converting to values and back
        km_key, km_mod = Gtk.accelerator_parse(shortcut)
        shortcut = Gtk.accelerator_name(km_key, km_mod)
        ref = None
        funcname = None
        if hasattr(func, 'im_self'):
            ref = weakref.ref(func.__self__)
            funcname = func.__name__
        else:
            ref = weakref.ref(func)
        self.__keymap[shortcut] = ref,funcname,args,kargs

    def handle_key_press_event(self, widget, event):
        """
        handles a key-press-event forwarded by any widget and calls the
        function stored for that accelerator, if existing. returns True
        if successful.
        """
        # remove numlock from the key modifiers
        key_mod = event.state & (~Gdk.MOD2_MASK)
        name = Gtk.accelerator_name(event.keyval, key_mod)
        if name == None:
            return False
        for shortcut, (ref,funcname,args,kargs) in self.__keymap.items():
            if shortcut == name:
                if funcname:
                    func = getattr(ref(), funcname)
                else:
                    func = ref()
                func(*args,**kargs)
                return True
        #print "unknown shortcut:",name
        return False

__all__ = [
    'is_frozen',
    'get_root_folder_path',
    'run_function_with_progress',
    'filepath',
    'db2linear',
    'linear2db',
    'format_time',
    'ticks_to_time',
    'prepstr',
    'fixbn',
    'bn2mn',
    'mn2bn',
    'note2str',
    'switch2str',
    'byte2str',
    'word2str',
    'roundint',
    'buffersize_to_latency',
    'filenameify',
    'read_int',
    'read_string',
    'write_int',
    'write_string',
    'from_hsb',
    'to_hsb',
    'question',
    'error',
    'message',
    'warning',
    'new_listview',
    'new_liststore',
    'new_combobox',
    'new_image_button',
    'get_item_count',
    'add_scrollbars',
    'file_filter',
    'format_filesize',
    'set_clipboard_text',
    'get_clipboard_text',
    'gettext',
    'diff',
    'is_effect',
    'is_generator',
    'is_controller',
    'is_root',
    'is_streamer',
    'get_new_pattern_name',
    'new_theme_image',
    'add_accelerator',
    'camelcase_to_unixstyle',
    'show_plugin_manual',
    ]

if __name__ == '__main__':
    oldlist = [1,2,6,3,4,5]
    newlist = [1,3,4,5,2]
    def insert_entry(i,o):
        print("insert",i,o)
        oldlist.insert(i,o)
    def del_entry(i):
        print("del",i)
        del oldlist[i]
    def swap_entry(i,j):
        print("swap",i,j)
        a,b = oldlist[i],oldlist[j]
        del oldlist[j]
        del oldlist[i]
        oldlist.insert(i,b)
        oldlist.insert(j,a)
    print(oldlist, newlist)
    synchronize_list(oldlist,newlist,insert_entry,del_entry,swap_entry)
    print(oldlist, newlist)


class ImageToggleButton(Gtk.ToggleButton):
    """
    GTK ToggleButton with Image 
    """
    def __init__(self, path, tooltip=None, width=20, height=20):
        self.image = Gtk.Image()
        self.image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(path, width, height))
        Gtk.ToggleButton.__init__(self)
        if tooltip:
            self.set_tooltip_text(tooltip)
        self.set_image(self.image)
