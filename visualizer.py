from typing import Any
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

from vocab import *

class PCol:
    CNONE = ''

    CEND      = '\33[0m'
    CBOLD     = '\33[1m'
    CITALIC   = '\33[3m'
    CURL      = '\33[4m'
    CBLINK    = '\33[5m'
    CBLINK2   = '\33[6m'
    CSELECTED = '\33[7m'

    CBLACK  = '\33[30m'
    CRED    = '\33[31m'
    CGREEN  = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE   = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE  = '\33[36m'
    CWHITE  = '\33[37m'
    CGREY   = '\33[90m'

    CBLACKBG  = '\33[40m'
    CREDBG    = '\33[41m'
    CGREENBG  = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG   = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG  = '\33[46m'
    CWHITEBG  = '\33[47m'

class Visualizer:
    def __init__(self):
        self.vocab:dict[str,list[Vocab]] = {}
        self.default_font = None
        self.bold_font = None
        self.italic_font = None
        self.headers = []
        self.vocab_info:dict[Vocab, dict[str, Any]] = {}
        self.vocab_expansion_callback = []
    
    def create_vocab_info_group(self, vocab:Vocab, toggle:int = 0):
        """
        Show/hide the vocab's information. Returns the group with the information. The group is put under `self.vocab_info[vocab]["group"]`

        If `toggle = 1` the info will be shown, if `toggle = -1` the info will be hidden, and if `toggle = 0` the info's visibility will be toggled
        """

        vocab_info_group = self.vocab_info[vocab]["expanded"]

        if vocab_info_group is not None and toggle != 1:
            dpg.delete_item(vocab_info_group)
            self.vocab_info[vocab]["expanded"] = None
            return None

        elif vocab_info_group is None and toggle != -1:
            with dpg.group(parent=self.vocab_info[vocab]["group"], horizontal=True) as vocab_info_group:
                dpg.add_spacer()
                dpg.add_spacer()

                with dpg.group():
                    self.vocab_info[vocab]["expanded"] = vocab_info_group
                    if isinstance(vocab, Verb):
                        if vocab.conjugations[Mood.Infinitive] is not None:
                            text_header = dpg.add_text("Infinitive")
                            dpg.bind_item_font(text_header, self.bold_font)
                            dpg.add_text(vocab.conjugations[Mood.Infinitive])
                            dpg.add_separator()

                        if vocab.conjugations[Mood.Indicative] is not None:
                            text_header = dpg.add_text("Indicative")
                            dpg.bind_item_font(text_header, self.bold_font)

                            with dpg.group(horizontal=True):
                                for tense in Tense:
                                    with dpg.group():
                                        dpg.add_text(tense.name)

                                        with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit,
                                            row_background=True, resizable=False, no_host_extendX=True, borders_innerV=True,
                                            delay_search=True, borders_outerV=True, borders_outerH=True):

                                            dpg.add_table_column()
                                            dpg.add_table_column(label="sg.")
                                            dpg.add_table_column(label="pl.")

                                            row_headers = ("1st", "2nd", "3rd",)

                                            for i, pers in enumerate(Person):
                                                with dpg.table_row():
                                                    dpg.add_text(row_headers[i])
                                                    for num in Number:
                                                        dpg.add_text(vocab.conjugations[Mood.Indicative][num+pers+tense])

                                    dpg.add_spacer()
                            dpg.add_separator()

                        if vocab.conjugations[Mood.Imperative] is not None:
                            text_header = dpg.add_text("Imperative")
                            dpg.bind_item_font(text_header, self.bold_font)
                            dpg.add_text(", ".join(vocab.conjugations[Mood.Imperative]))
                            dpg.add_separator()
                    
                    dpg.add_spacer()

                    return vocab_info_group
            
        return vocab_info_group
    
    def create_vocab_list_window(self):
        with dpg.window(label="Vocab List", tag="VocabList") as window:
            dpg.bind_item_theme(window, "vocab_info_inner_group_theme")
            with dpg.menu_bar():
                with dpg.menu(label="Menu"):
                    dpg.add_menu_item(label="Load")
                    dpg.add_menu_item(label="Save")
                    dpg.add_menu_item(label="Save As")

                def expand_all():
                    for header in self.headers:
                        dpg.set_value(header, True)
                    for callback in self.vocab_expansion_callback:
                        callback(1)
                
                def collapse_all():
                    for header in self.headers:
                        dpg.set_value(header, False)
                    for callback in self.vocab_expansion_callback:
                        callback(-1)

                dpg.add_menu_item(label="Expand all", callback=expand_all)
                dpg.add_menu_item(label="Collapse all", callback=collapse_all)

            for header_text, vocab_list in self.vocab.items():
                with dpg.collapsing_header(label=header_text, default_open=True) as header:
                    self.headers.append(header)
                    for vocab in vocab_list:
                        with dpg.group() as vocab_group:
                            self.vocab_info[vocab] = {"group": vocab_group, "expanded": None}

                            cb = lambda _1, _2, voc: self.create_vocab_info_group(voc, 0)
                            cb_dat = vocab
                            self.vocab_expansion_callback.append(lambda toggle=0, cb_dat=cb_dat: self.create_vocab_info_group(cb_dat, toggle))

                            with dpg.group(horizontal=True, horizontal_spacing=0):

                                for s in vocab.description.split(PCol.CEND):
                                    theme = None
                                    font = None

                                    s = s.replace(PCol.CEND, "")

                                    i = 0
                                    if (i := s.find(PCol.CVIOLET)) != -1:
                                        theme = "vocab_theme"
                                    elif (i := s.find(PCol.CBLUE)) != -1:
                                        theme = "definition_theme"
                                        font = self.italic_font
                                    elif (i := s.find(PCol.CRED)) != -1:
                                        theme = "latin_theme"
                                        font = self.bold_font
                                    elif (i := s.find(PCol.CGREY)) != -1:
                                        theme = "debug_info_theme"
                                        if i != 0:
                                            dpg.add_button(label=s[:i], callback=cb, user_data=cb_dat)
                                        continue

                                    s = s.replace(PCol.CVIOLET, "")
                                    s = s.replace(PCol.CBLUE, "")
                                    s = s.replace(PCol.CRED, "")
                                    s = s.replace(PCol.CGREY, "")

                                    if i != 0:
                                        text = dpg.add_button(label=s[:i], callback=cb, user_data=cb_dat)
                                        s = s[i:]

                                    text = dpg.add_button(label=s, callback=cb, user_data=cb_dat)
                                    if theme is not None: dpg.bind_item_theme(text, theme)
                                    if font is not None: dpg.bind_item_font(text, font)

    def visualize(self):
        dpg.create_context()

        with dpg.theme(tag="vocab_theme"):
            with dpg.theme_component():
                dpg.add_theme_color(dpg.mvThemeCol_Text, [236, 29, 236])

        with dpg.theme(tag="latin_theme"):
            with dpg.theme_component():
                dpg.add_theme_color(dpg.mvThemeCol_Text, [236, 151, 29])
        
        with dpg.theme(tag="definition_theme"):
            with dpg.theme_component():
                dpg.add_theme_color(dpg.mvThemeCol_Text, [80, 181, 255])

        with dpg.theme(tag="debug_info_theme"):
            with dpg.theme_component():
                dpg.add_theme_color(dpg.mvThemeCol_Text, [151, 151, 151])
            
        with dpg.font_registry():
            with dpg.font("fonts/NotoSans-Medium.ttf", 30) as self.default_font:
                dpg.add_font_range(0x0020, 0x01FF)
                dpg.bind_font(self.default_font)
            with dpg.font("fonts/NotoSans-Bold.ttf", 30) as self.bold_font:
                dpg.add_font_range(0x0020, 0x01FF)
            with dpg.font("fonts/NotoSans-Italic.ttf", 30) as self.italic_font:
                dpg.add_font_range(0x0020, 0x01FF)
            dpg.set_global_font_scale(0.5)

        dpg.create_viewport(title='Latin Study')

        # with dpg.window(label="Vocab List", tag="VocabList"):
        #     dpg.add_text("List!")
        self.create_vocab_list_window()

        demo.show_demo()
        dpg.show_font_manager()

        dpg.setup_dearpygui()
        # dpg.set_primary_window("VocabList", True)
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    Visualizer().visualize()