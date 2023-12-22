#!/usr/bin/python
# coding: utf-8

import locale, gettext, os, struct

try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

import gi

gi.require_versions({'Gtk': '3.0', 'Nemo': '3.0'})
from gi.repository import GObject, Gtk, Nemo

regions = {
                "C": "China",
                "D": "German",
                "E": "USA",
                "F": "France",
                "H": "Holland",
                "I": "Italy",
                "O": "International",
                "J": "Japan",
                "K": "Korea",
                "N": "Netherlands",
                "P": "Europe",
                "R": "Russia",
                "S": "Spain",
                "U": "Australia",
                "V": "Europe",
                "W": "Europe",
                "X": "Europe"
        }

def get_rom_info(filename):
    ext = os.path.splitext(filename)[-1].lower()
    if ext != '.nds':
        return {}

    with open(filename, "rb") as f:
        pattern = '12s 4s 2s 1b 1b 1b 8x 1b 1b'
        header_len = struct.calcsize(pattern)
        header = f.read(header_len)
        h_struct = struct.unpack(pattern, header)
        info = {
                    "Short Title": h_struct[0].decode("ascii").strip('\x00'),
                    "Product Code": h_struct[1].decode("ascii"), 
                    "Maker Code": h_struct[2].decode('ascii'),
                    # "Region": h_struct[6], #header has field but only applies to Korean & Chinese games
                    "Region": regions.get(h_struct[1].decode("ascii")[-1], "Unknown"), #Lookup last letter of Product Code,
                    "DSi Enhanced": str(h_struct[3] > 0),
                    "Storage Capacity": str(int((2**h_struct[5])/8)) + "MB",
                    "Version": str(h_struct[7]),
               }

        try:
            # banner_length = 2112
            f.seek(104, 0) #Seek to location of banner's offset
            banner_offset_bytes = f.read(4)[::-1] # 4 bytes Reversed endianess
            banner_offset = int.from_bytes(banner_offset_bytes)
            # print("Banner Offset", banner_offset)
            titles_offset = 576
            title_length = 256
            f.seek(banner_offset + titles_offset, 0)

            banners = {} #Store every unique banner language
            languages = ["Japanese", "English", "French", "German", "Itallian", "Spanish"]
            for lang in languages:
                banner_title = f.read(title_length)
                text = banner_title.decode('utf_16').replace('\x00', '').strip()
                if text and text not in banners.values():
                    banners[lang + " Banner"] = text

            if len(banners) == 1: #All languages have same banner, insert text under generic "Banner" key
                info["Banner"] = list(banners.values())[0]
            elif len(banners) >= 2: #Many unique banners. Merge Banner and info dicts
                info = {**info, **banners}
        except:
            pass

        print(info)
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


class NintendoNDSinfoPropertyPage(GObject.GObject, Nemo.PropertyPageProvider, Nemo.NameAndDescProvider):

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

        self.property_label = Gtk.Label(_('NDS Info'))
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

        return Nemo.PropertyPage(name="NemoPython::NDSinfo", label=self.property_label, page=self.mainWindow),

    def get_name_and_desc(self):
        return [("Nemo NDS Info Tab:::View Nintendo DS information from the properties tab")]
