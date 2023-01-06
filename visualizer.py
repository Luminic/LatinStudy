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

class FilterMenu:
    def __init__(self, visualiser):
        self.visualiser = visualiser
        self.vocab_types_active: dict[type|str, bool] = {}

        self.text_input_group = None
        self.text_input_rows = []

        self.create()
    
    def remove_text_input_row(self, input_row):
        try:
            self.text_input_rows.remove(input_row)
            dpg.delete_item(input_row)
        except ValueError:
            pass

        if len(self.text_input_rows) == 0:
            self.create_text_input_row()
    
    def create_text_input_row(self):
        with dpg.table_row(parent=self.text_input_group) as input_row:
            dpg.add_button(label="X", callback=lambda s, a, u: self.remove_text_input_row(u), user_data=input_row)
            dpg.add_input_text(width=-1)
            dpg.add_combo(("Off", "Word", "Word Beginning", "Word End"), default_value="Off", width=100)
            dpg.add_combo(("Any", "Latin", "Definition"), default_value="Any", width=100)
            self.text_input_rows.append(input_row)

    def create(self):
        with dpg.child_window(label="Filters", autosize_x=True, height=150) as filter_menu:
            self.filter_menu = filter_menu

            dpg.add_text("Filters")

            vocab_types = [Noun, Verb, Adjective, "Other"]
            for vocab_type in vocab_types:
                self.vocab_types_active[vocab_type] = True

            def vocab_type_activity_callback(vocab_type, value):
                self.vocab_types_active[vocab_type] = value
                self.visualiser.update_visiblity()

            with dpg.group(horizontal=True):
                for vocab_type in vocab_types:
                    dpg.add_checkbox(
                        label=vocab_type.__name__ if type(vocab_type) is type else vocab_type,
                        default_value=True,
                        callback=lambda _, val, dat: vocab_type_activity_callback(dat, val),
                        user_data=vocab_type
                    )
            
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit) as self.text_input_group:
                dpg.add_table_column(label="")
                dpg.add_table_column(label="Match Text", width_stretch=True)
                dpg.add_table_column(label="Word matching")
                dpg.add_table_column(label="Text type")
            
            for i in range(5):
                self.create_text_input_row()
            
            dpg.add_button(label="Add Row", callback=self.create_text_input_row)
    
    def should_be_visible(self, vocab:Vocab) -> bool:
        if (active := self.vocab_types_active.get(type(vocab))) is not None:
            if not active:
                return False
        else:
            if not self.vocab_types_active["Other"]:
                return False
        
        return True

class Visualizer:
    def __init__(self):
        self.vocab:dict[str,list[Vocab]] = {}

        self.default_font = None
        self.bold_font = None
        self.italic_font = None

        self.vocab_window = None
        self.filter_menu = None
        self.headers = []
        self.vocab_info:dict[Vocab, dict[str, Any]] = {}
        self.vocab_expansion_callback = []
    
    def create_verb_info_group(self, verb:Verb):
        with dpg.group() as verb_info_group:
            if verb.conjugations[Mood.Infinitive] is not None:
                text_header = dpg.add_text("Infinitive")
                dpg.bind_item_font(text_header, self.bold_font)
                dpg.add_text(verb.conjugations[Mood.Infinitive])
                dpg.add_separator()

            if verb.conjugations[Mood.Indicative] is not None:
                text_header = dpg.add_text("Indicative")
                dpg.bind_item_font(text_header, self.bold_font)

                with dpg.group(horizontal=True):
                    for tense in Tense:
                        with dpg.group():
                            dpg.add_text(tense.name)

                            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit,
                                    row_background=True, resizable=False, no_host_extendX=True,
                                    borders_innerV=True, delay_search=True, borders_outerV=True,
                                    borders_outerH=True):

                                dpg.add_table_column()
                                dpg.add_table_column(label="sg.")
                                dpg.add_table_column(label="pl.")

                                row_headers = ("1st", "2nd", "3rd",)

                                for i, pers in enumerate(Person):
                                    with dpg.table_row():
                                        dpg.add_text(row_headers[i])
                                        for num in Number:
                                            dpg.add_text(verb.conjugations[Mood.Indicative][num+pers+tense])

                        dpg.add_spacer()
                dpg.add_separator()

            if verb.conjugations[Mood.Imperative] is not None:
                text_header = dpg.add_text("Imperative")
                dpg.bind_item_font(text_header, self.bold_font)
                dpg.add_text(", ".join(verb.conjugations[Mood.Imperative]))
                dpg.add_separator()
            
            dpg.add_spacer()
            return verb_info_group

    def create_declension_table(self, cases:list[str]):
        with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit,
                row_background=True, resizable=False, no_host_extendX=True, borders_innerV=True,
                delay_search=True, borders_outerV=True, borders_outerH=True) as decl_table:
            dpg.add_table_column()
            dpg.add_table_column(label="sg.")
            dpg.add_table_column(label="pl.")

            row_headers = ("nom", "gen", "dat", "acc", "abl", "voc")

            for i, case, in enumerate(Case):
                with dpg.table_row():
                    dpg.add_text(row_headers[i])
                    for num in Number:
                        dpg.add_text(cases[case + num])

            return decl_table

    def create_noun_info_group(self, noun:Noun):
        with dpg.group() as noun_info_group:
            th_ending = lambda x: ("st", "nd", "rd")[x-1] if 1 <= x <= 3 else "th"
            text_header = dpg.add_text(f"{noun.declension}{th_ending(noun.declension)}-declension {noun.gender.name.lower()} noun:")
            dpg.bind_item_font(text_header, self.bold_font)
            
            self.create_declension_table(noun.cases)

            dpg.add_spacer()
            return noun_info_group
    
    def create_vocab_info_group(self, vocab:Vocab):
        """
        Creates and returns the group with the vocab's information.
        
        The info group is put in `self.vocab_info[vocab]["group"]`

        If the info group is already created it will just return the group
        """

        if (vocab_info_group := self.vocab_info[vocab]["info-group"]) != None:
            return vocab_info_group

        with dpg.group(parent=self.vocab_info[vocab]["group"], horizontal=True) as vocab_info_group:
            dpg.add_spacer()
            dpg.add_spacer()
            self.vocab_info[vocab]["info-group"] = vocab_info_group

            if isinstance(vocab, Verb):
                self.create_verb_info_group(vocab)

            if isinstance(vocab, Noun):
                self.create_noun_info_group(vocab)
            
            self.vocab_info[vocab]["expanded"] = True
            
            return vocab_info_group
    
    def toggle_vocab_info_group(self, vocab:Vocab, toggle:int = 0):
        """
        Show/hide the vocab's information. If the info group hasn't been created yet it will create the info group
        """

        expanded = self.vocab_info[vocab]["expanded"]
        vocab_info_group = self.create_vocab_info_group(vocab)

        if expanded and toggle != 1:
            dpg.hide_item(vocab_info_group)
            self.vocab_info[vocab]["expanded"] = False
        elif not expanded and toggle != -1:
            dpg.show_item(vocab_info_group)
            self.vocab_info[vocab]["expanded"] = True
    
    def create_vocab_list_window(self):
        with dpg.window(label="Vocab List", tag="VocabList", horizontal_scrollbar=True) as self.vocab_window:
            # dpg.bind_item_theme(self.window, "vocab_info_inner_group_theme")
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
            
            self.filter_menu = FilterMenu(self)

            for header_text, vocab_list in self.vocab.items():
                with dpg.collapsing_header(label=header_text, default_open=True) as header:
                    self.headers.append(header)
                    for vocab in vocab_list:
                        with dpg.group() as vocab_group:
                            self.vocab_info[vocab] = {"group": vocab_group, "info-group": None, "expanded": False}

                            cb = lambda _1, _2, voc: self.toggle_vocab_info_group(voc, 0)
                            cb_dat = vocab
                            self.vocab_expansion_callback.append(
                                lambda toggle=0, cb_dat=cb_dat: self.toggle_vocab_info_group(cb_dat, toggle)
                            )

                            with dpg.group(horizontal=True, horizontal_spacing=0):

                                for s in vocab.description.split(PCol.CEND):
                                    theme = None
                                    font = None

                                    s = s.replace(PCol.CEND, "")

                                    i = 0
                                    if (i := s.find(PCol.CVIOLET)) != -1:
                                        s = s.replace(PCol.CVIOLET, "")
                                        theme = "vocab_theme"

                                    elif (i := s.find(PCol.CRED)) != -1:
                                        s = s.replace(PCol.CRED, "")
                                        theme = "latin_theme"
                                        font = self.bold_font

                                    elif (i := s.find(PCol.CBLUE)) != -1:
                                        s = s.replace(PCol.CBLUE, "")
                                        theme = "definition_theme"
                                        font = self.italic_font

                                    elif (i := s.find(PCol.CYELLOW)) != -1:
                                        s = s.replace(PCol.CYELLOW, "")
                                        theme = "gender_theme"

                                    elif (i := s.find(PCol.CGREY)) != -1:
                                        s = s.replace(PCol.CGREY, "")
                                        theme = "debug_info_theme"
                                        if i != 0:
                                            dpg.add_button(label=s[:i], callback=cb, user_data=cb_dat)
                                        continue

                                    if i != 0:
                                        text = dpg.add_button(label=s[:i], callback=cb, user_data=cb_dat)
                                        s = s[i:]

                                    text = dpg.add_button(label=s, callback=cb, user_data=cb_dat)
                                    if theme is not None: dpg.bind_item_theme(text, theme)
                                    if font is not None: dpg.bind_item_font(text, font)
        
        with dpg.handler_registry():
            dpg.add_key_press_handler(key=dpg.mvKey_F, callback=lambda a,b: print(a))

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
        
        with dpg.theme(tag="gender_theme"):
            with dpg.theme_component():
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 0])

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
    
    def update_visiblity(self):
        for header, vocab_list in self.vocab.items():
            for vocab in vocab_list:
                vocab_group = self.vocab_info[vocab]["group"]
                if self.filter_menu.should_be_visible(vocab):
                    dpg.show_item(vocab_group)
                else:
                    dpg.hide_item(vocab_group)

if __name__ == "__main__":
    Visualizer().visualize()