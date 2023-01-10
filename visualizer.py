from __future__ import annotations
import string

from typing import Any, Callable
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

from vocab import *


class TextFilter:
    def __init__(self):
        self.table_row = None
    
    def __eq__(self, other: TextFilter):
        if not isinstance(other, TextFilter):
            raise ValueError
        return self.table_row == other.table_row
    
    def create(self, parent=None, deletion_callback:Callable=None, filter_change_callback:Callable=None):
        with dpg.table_row(parent=parent) as self.table_row:
            dpg.add_button(label="X", callback=deletion_callback, user_data=self)
            self.text_input = dpg.add_input_text(width=-1, callback=filter_change_callback)
            self.search_parsings_checkbox = dpg.add_checkbox(callback=filter_change_callback)
            self.match_case_checkbox = dpg.add_checkbox(callback=filter_change_callback)
            self.match_diacritics_checkbox = dpg.add_checkbox(callback=filter_change_callback)
            self.word_match_combo = dpg.add_combo(("Off", "Word", "Word Beginning", "Word Ending"), default_value="Off", width=100, callback=filter_change_callback)
            self.text_type_combo = dpg.add_combo(("Any", "Latin", "Definition"), default_value="Any", width=100, callback=filter_change_callback)
        
        return self.table_row
    
    def destroy(self):
        dpg.delete_item(self.table_row)
    
    def should_be_visible(self, vocab:Vocab) -> bool:
        match dpg.get_value(self.text_type_combo):
            case "Latin":
                descs = [d for (d,dt) in vocab.get_parsed_description() if dt == DescBlockType.Latin]
            case "Definition":
                descs = [d for (d,dt) in vocab.get_parsed_description() if dt == DescBlockType.Definition]
            case _:
                descs = [vocab.get_clean_description()]

        if dpg.get_value(self.search_parsings_checkbox):
            descs.append(vocab.get_extended_description())

        to_match = dpg.get_value(self.text_input)

        if not dpg.get_value(self.match_case_checkbox):
            descs = [d.lower() for d in descs]
            to_match = to_match.lower()
        
        if not dpg.get_value(self.match_diacritics_checkbox):
            descs = [make_short(d) for d in descs]
            to_match = make_short(to_match)

        for desc in descs:
            for i in range(len(desc) - len(to_match) + 1):
                if desc[i:i+len(to_match)] == to_match:
                    match dpg.get_value(self.word_match_combo):
                        case "Word":
                            if i >= 1 and desc[i-1] in string.ascii_letters:
                                continue
                            elif i < len(desc) - len(to_match) and desc[i+len(to_match)] in string.ascii_letters:
                                continue
                        case "Word Beginning":
                            if i >= 1 and desc[i-1] in string.ascii_letters:
                                continue
                        case "Word Ending":
                            if i < len(desc) - len(to_match) and desc[i+len(to_match)] in string.ascii_letters:
                                continue

                    return True
        return False


class FilterMenu:
    def __init__(self, visualiser: Visualizer):
        self.visualiser = visualiser
        self.vocab_types_active: dict[type|str, bool] = {}

        self.text_filter_group = None
        self.text_filters:list[TextFilter] = []

        self.create()
    
    def remove_text_input_row(self, _s, _a, text_filter: TextFilter):
        for i in range(len(self.text_filters)):
            if self.text_filters[i] == text_filter:
                self.text_filters.pop(i).destroy()
                break
        self.create_text_input_row()
        self.visualiser.update_visiblity()
    
    def create_text_input_row(self):
        tf = TextFilter()
        tf.create(
            parent=self.text_filter_group,
            deletion_callback=self.remove_text_input_row,
            filter_change_callback=self.visualiser.update_visiblity
        )
        self.text_filters.append(tf)

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
            
            with dpg.table(header_row=True, policy=dpg.mvTable_SizingFixedFit) as self.text_filter_group:
                dpg.add_table_column(label="")
                dpg.add_table_column(label="Match Text", width_stretch=True)
                dpg.add_table_column(label="Search parsings")
                dpg.add_table_column(label="Match case")
                dpg.add_table_column(label="Match diacritics")
                dpg.add_table_column(label="Word matching")
                dpg.add_table_column(label="Text type")
            
            self.create_text_input_row()
            
            dpg.add_button(label="Add Row", width=-1, callback=self.create_text_input_row)
    
    def should_be_visible(self, vocab:Vocab) -> bool:
        if (active := self.vocab_types_active.get(type(vocab))) is not None:
            if not active:
                return False
        else:
            if not self.vocab_types_active["Other"]:
                return False
        
        for filter in self.text_filters:
            if not filter.should_be_visible(vocab):
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
                                for desc, desc_type in vocab.get_parsed_description():
                                    theme = None
                                    font = None
                                    match desc_type:
                                        case DescBlockType.Text:
                                            pass
                                        case DescBlockType.VocabType:
                                            theme = "vocab_theme"
                                        case DescBlockType.Latin:
                                            theme = "latin_theme"
                                            font = self.bold_font
                                        case DescBlockType.Definition:
                                            theme = "definition_theme"
                                            font = self.italic_font
                                        case DescBlockType.Gender:
                                            theme = "gender_theme"
                                        case DescBlockType.DebugInfo:
                                            theme = "debug_info_theme"
                                            continue
                                    
                                    text = dpg.add_button(label=desc, callback=cb, user_data=cb_dat)
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