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

from neil.utils import Menu, test_view
from gi.repository import GObject, Gtk, Pango
import inspect
import neil.com as com
import neil.contextlog as contextlog
import os

MARGIN = 6


class PackageBrowserDialog(Gtk.Dialog):
    __neil__ = dict(
        id = 'neil.componentbrowser.dialog',
        singleton = True,
    )

    def __init__(self, hide_on_delete=True):
        Gtk.Dialog.__init__(self, "Component Browser")
        if hide_on_delete:
            self.connect('delete-event', self.hide_on_delete)
        self.resize(600, 500)
        #self.ifacestore = Gtk.TreeStore(GdkPixbuf, str, GObject.TYPE_PYOBJECT)
        self.ifacestore = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT)
        self.ifacelist = Gtk.TreeView(self.ifacestore)
        self.ifacelist.set_property('headers-visible', False)
        column = Gtk.TreeViewColumn("Item")
        #~ cell = Gtk.CellRendererPixbuf()
        #~ column.pack_start(cell, False)
        #~ column.set_attributes(cell, pixbuf=0)
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.set_attributes(cell, markup=0)
        self.ifacelist.append_column(column)

        # def resolve_path(path):
        #     if exthost:
        #         return exthost.resolve_path(path)
        #     else:
        #         return path
        self.desc = Gtk.TextView()
        self.desc.set_wrap_mode(Gtk.WrapMode.WORD)
        self.desc.set_editable(False)
        #self.desc.set_justification(Gtk.JUSTIFY_FILL)
        textbuffer = self.desc.get_buffer()
        textbuffer.create_tag("i", style=Pango.STYLE_ITALIC)
        textbuffer.create_tag("u", underline=Pango.Underline.SINGLE)
        textbuffer.create_tag("b", weight=Pango.Weight.BOLD)

        rootnode = self.ifacestore.append(None, ["<b>Neil Components</b>", None])
        packagenode = self.ifacestore.append(rootnode, ["<b>By Packages</b>", None])
        pkgnodes = {}
        pkgnodes['(unknown)'] = self.ifacestore.append(packagenode, ["<i>(unknown)</i>", None])
        for pkg in sorted(com.get_packages(), lambda a, b: cmp(a.name.lower(), b.name.lower())):
            pkgnodes[pkg.module] = self.ifacestore.append(packagenode, ["<b>%s</b> (<b>module</b> <i>%s</i>)" % (pkg.name, pkg.module), None])
        categorynode = self.ifacestore.append(rootnode, ["<b>By Categories</b>", None])
        catnodes = {}
        catnodes['(unknown)'] = self.ifacestore.append(categorynode, ["<i>(unknown)</i>", None])
        for name in sorted(com.get_categories()):
            catnodes[name] = self.ifacestore.append(categorynode, ["<b>category</b> <i>%s</i>" % name, None])
        allnode = self.ifacestore.append(rootnode, ["<b>By Alphabet</b>", None])

        def create_classnode(parent, metainfo):
            element = metainfo.get('classobj', None)
            if not element:
                return
            classname = element.__neil__['id']
            ifacenode = self.ifacestore.append(parent, ["<b>component</b> %s" % classname, element])
            for ename in dir(element):
                eelement = getattr(element, ename)
                if not ename.startswith('_') and inspect.ismethod(eelement):
                    methodnode = self.ifacestore.append(ifacenode, ["<b>method</b> %s" % ename, eelement])
        for name in sorted(com.get_factories()):
            metainfo = com.get_factories()[name]
            create_classnode(allnode, metainfo)
            modulename = metainfo.get('modulename', None) or '(unknown)'
            if modulename in pkgnodes:
                create_classnode(pkgnodes[modulename], metainfo)
            for category in metainfo.get('categories', []):
                if category in catnodes:
                    create_classnode(catnodes[category], metainfo)
        hsizer = Gtk.HPaned()
        hsizer.set_border_width(MARGIN)
        scrollwin = Gtk.ScrolledWindow()
        scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrollwin.set_shadow_type(Gtk.ShadowType.IN)
        scrollwin.add(self.ifacelist)
        hsizer.pack1(scrollwin)
        scrollwin = Gtk.ScrolledWindow()
        scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrollwin.set_shadow_type(Gtk.ShadowType.IN)
        scrollwin.add(self.desc)
        hsizer.pack2(scrollwin)
        hsizer.set_position(300)
        self.vbox.add(hsizer)
        self.ifacelist.get_selection().connect('changed', self.on_ifacelist_sel_changed)
        self.ifacelist.connect('row-activated', self.on_ifacelist_row_activated)
        self.ifacelist.connect('button-press-event', self.on_ifacelist_button_press_event)
        self.on_ifacelist_sel_changed(self.ifacelist.get_selection())

    def on_ifacelist_button_press_event(self, widget, event):
        res = widget.get_path_at_pos(int(event.x), int(event.y))
        if not res:
            return
        path, col, x, y = res
        model = widget.get_model()
        it = model.get_iter(path)
        obj = model.get_value(it, 1)
        if not obj:
            return
        if event.button == 3:
            menu = Menu()
            classname = obj.__neil__['id']
            menu.add_item("Test '" + classname + "'", self.test_view, classname)
            menu.popup(self, event)

    def test_view(self, menuitem, classname):
        test_view(classname)

    def cleanup_docstr(self, docstr):
        """
        returns a cleaned up epydoc-compatible docstring suitable
        for output in an editbox.
        """
        assert docstr != None

        def wrap(lines):
            if lines and not lines[0]:
                del lines[0]
            if lines and not lines[-1]:
                del lines[-1]
            s = ''
            for l in lines:
                l = l.strip()
                if s and not l:
                    s += '\n'
                elif l:
                    if s:
                        s += ' '
                    s += l
            return s

        import re
        rcmp = re.compile(r'^\@([\s\w]+):(.*)$')
        desc = None
        cb = []
        targets = []
        ctarg = None
        for line in docstr.split('\n'):
            line = line.strip()
            m = rcmp.match(line)
            if m:
                if not desc:
                    desc = wrap(cb)
                    cb = []
                if ctarg:
                    targets.append((ctarg, wrap(cb)))
                    ctarg = None
                    cb = []
                t, line = m.group(1), m.group(2)
                ctarg = t
            cb.append(line)
        if not desc:
            desc = wrap(cb)
        if ctarg:
            targets.append((ctarg, wrap(cb)))
        params = {}
        pcmp1 = re.compile(r'^\s*(\w+)\s+(\w+)\s*$')
        for ptarg, pdesc in targets:
            m = pcmp1.match(ptarg)
            if not m:
                params[ptarg] = pdesc
            else:
                params[(m.group(1), m.group(2))] = pdesc
        return desc, params

    def on_ifacelist_row_activated(self, widget, path, column):
        store, rows = widget.get_selection().get_selected()
        if not rows:
            return
        obj = store.get(rows, 1)[0]
        if not obj:
            return
        try:
            filepath = inspect.getsourcefile(obj)
            source, line = inspect.getsourcelines(obj)
        except TypeError:
            return
        os.spawnlp(os.P_NOWAIT, 'scite', 'scite', '-open:' + filepath, '-goto:' + str(line))

    def on_ifacelist_sel_changed(self, selection):
        """
        Handles changes in the treeview. Updates meta information.
        """
        buffer = self.desc.get_buffer()
        buffer.set_text("")
        iter = buffer.get_iter_at_offset(0)

        def insert(a, b=None):
            if b:
                buffer.insert_with_tags_by_name(iter, a, b)
            else:
                buffer.insert(iter, a)
        store, rows = selection.get_selected()
        if not rows:
            insert("Select a component or method to see a description.", 'i')
            return
        obj = store.get(rows, 1)[0]
        if not obj:
            insert("Select a component or method to see a description.", 'i')
            return
        keyw = 'b'
        paramc = 'i'
        funcc = 'u'
        defvc = 'i'
        docstr = ""
        filepath = ''
        source, line = [], 1
        try:
            filepath = inspect.getsourcefile(obj)
            source, line = inspect.getsourcelines(obj)
        except TypeError:
            pass
        if filepath:
            # print reference to stdout so devs can click the line from
            # within SciTE.
            contextlog.clean_next_line()
            print(("%s:%s:%r" % (filepath, line, obj)))
        insert('File "%s", Line %s\n\n' % (filepath, line), 'i')
        if inspect.ismethod(obj):
            docstr = ""
            if hasattr(obj, '__doc__'):
                docstr = obj.__doc__ or ""
            insert("def ", keyw)
            args, varargs, varkw, defaults = inspect.getargspec(obj)
            if not defaults:
                defaults = []
            if len(defaults) < args:
                defaults = [None] * (len(args) - len(defaults)) + list(defaults)
            insert(obj.__func__.__name__, funcc)
            insert("(")
            index = 0
            for arg, df in zip(args, defaults):
                if index:
                    insert(', ')
                insert(arg)
                if df != None:
                    insert('=%r' % df, defvc)
                index += 1
            insert(')\n\n')
        elif inspect.isclass(obj):
            docstr = ""
            if hasattr(obj, '__doc__'):
                docstr = obj.__doc__ or ""
            insert('class ', keyw)
            insert(obj.__name__)
            insert(':\n\n')
        else:
            return
        desc, params = self.cleanup_docstr(docstr)
        if desc:
            insert('%s\n\n' % desc)
        if params:
            args, varargs, varkw, defaults = inspect.getargspec(obj)
            for arg in args[1:]:
                desc = params.get(('param', arg), 'No description.')
                typedesc = params.get(('type', arg), 'Unknown')
                insert('%s (%s):' % (arg, typedesc), paramc)
                insert('\t%s\n' % desc)
            desc = params.get('return', 'No description.')
            typedesc = params.get('rtype', 'Unknown')
            insert('returns (%s):' % typedesc, paramc)
            insert('\t%s\n' % desc)


class PackageBrowserMenuItem:
    __neil__ = dict(
        id = 'neil.componentbrowser.menuitem',
        singleton = True,
        categories = [
            'menuitem.tool'
        ],
    )

    def __init__(self, menu):
        # create a menu item
        item = Gtk.MenuItem(label="Show _Component Browser")
        # connect the menu item to our handler
        item.connect('activate', self.on_menuitem_activate)
        # append the item to the menu
        menu.append(item)

    def on_menuitem_activate(self, widget):
        browser = com.get('neil.componentbrowser.dialog')
        browser.show_all()

__neil__ = dict(
    classes = [
        PackageBrowserDialog,
        PackageBrowserMenuItem,
    ],
)

if __name__ == '__main__':  # extension mode
    browser = PackageBrowserDialog(False)
    browser.connect('destroy', lambda widget: Gtk.main_quit())
    browser.show_all()
    Gtk.main()
