#!/usr/bin/python
# coding: utf-8

import locale, gettext, os

try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

import gi

gi.require_versions({'Gtk': '3.0', 'Nemo': '3.0'})
from gi.repository import GObject, Gtk, Nemo


def get_rom_info(filename):
    ext = os.path.splitext(filename)[-1].lower()
    if ext in ['.3ds', '.cci']:
        from pyctr.type.cci import CCIReader as Reader
        from pyctr.type.cci import CCISection as Section
    elif ext == '.cia':
        from pyctr.type.cia import CIAReader as Reader
        from pyctr.type.cia import CIASection as Section
    elif ext == '.cxi':
        from pyctr.type.ncch import NCCHReader as Reader
        from pyctr.type.ncch import NCCHSection as Section
    else:
        return {}

    LANGUAGE = "English"
    with Reader(filename) as rom:
        if ext == '.cxi':
            prod_info = rom
        else:  # '.cia' or '.3ds'
            prod_info = rom.contents[Section.Application]

        app_title = prod_info.exefs.icon.get_app_title(LANGUAGE)

        info = {'Application Title': app_title.short_desc,
                'Application Description': app_title.long_desc.replace('\n', ' '),
                'Application Publisher': app_title.publisher,
                'Product Code': prod_info.product_code,
                'Program ID': prod_info.program_id}

        if ext == '.cia':
            info['Title Version'] = '{0.major}.{0.minor}.{0.micro}'.format(rom.tmd.title_version)

    return info


GUI = """
<interface>
  <requires lib="gtk+" version="3.0"/>
  <object class="GtkScrolledWindow" id="mainWindow">
    <property name="visible">True</property>
    <property name="can_focus">True</property>
    <property name="hscrollbar_policy">never</property>
    <child>
      <object class="GtkViewport" id="viewport1">
        <property name="visible">True</property>
        <property name="can_focus">False</property>
        <child>
          <object class="GtkGrid" id="grid">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <property name="vexpand">True</property>
            <property name="row_spacing">4</property>
            <property name="column_spacing">16</property>
          </object>
        </child>
      </object>
    </child>
  </object>
</interface>"""


class Nintendo3dsinfoPropertyPage(GObject.GObject, Nemo.PropertyPageProvider, Nemo.NameAndDescProvider):

    def get_property_pages(self, files):
        # files: list of NemoVFSFile
        if len(files) != 1:
            return

        file = files[0]
        if file.get_uri_scheme() != 'file':
            return

        if file.is_directory():
            return

        filename = unquote(file.get_uri()[7:])

        try:
            filename = filename.decode("utf-8")
        except:
            pass

        info = get_rom_info(filename)
        if not info:
            return

        locale.setlocale(locale.LC_ALL, '')
        gettext.bindtextdomain("nemo-extensions")
        gettext.textdomain("nemo-extensions")
        _ = gettext.gettext

        self.property_label = Gtk.Label(_('3DS Info'))
        self.property_label.show()

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('nemo-extensions')
        self.builder.add_from_string(GUI)

        self.mainWindow = self.builder.get_object("mainWindow")
        self.grid = self.builder.get_object("grid")

        # print(info)

        for i, (key, val) in enumerate(info.items()):
            label = Gtk.Label()
            label.set_markup(f"<b>{key}:</b>")
            label.set_justify(Gtk.Justification.LEFT)
            label.set_halign(Gtk.Align.START)
            label.show()
            self.grid.attach(label, 0, i, 1, 1)
            label = Gtk.Label()
            label.set_text(val)
            label.set_justify(Gtk.Justification.LEFT)
            label.set_halign(Gtk.Align.START)
            label.set_selectable(True)
            label.set_line_wrap(False)
            label.set_line_wrap_mode(2)  # PANGO_WRAP_WORD_CHAR
            # label.set_max_width_chars(160)
            label.show()
            self.grid.attach(label, 1, i, 1, 1)

        return Nemo.PropertyPage(name="NemoPython::3DSinfo", label=self.property_label, page=self.mainWindow),

    def get_name_and_desc(self):
        return [("Nemo 3DS Info Tab:::View 3DS information from the properties tab")]
