from __future__ import annotations

from html.parser import HTMLParser
from typing import TypeAlias
import string

import vocab
import logging


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


def expand_html(html: str) -> str:
    depth = 0
    expanded_html = []
    for i, char in enumerate(html):
        if char == '<':
            expanded_html.append('\n')
            if i + 1 < len(html):
                if i + 5 < len(html) and html[i+1:i+5] == "meta":
                    pass
                    expanded_html.append('\t'*depth)
                elif html[i+1] == '/':
                    depth -= 1
                    expanded_html.append('\t'*depth)
                else:
                    expanded_html.append('\t'*depth)
                    depth += 1
        
        elif i-1 > 0 and  html[i-1] == '>':
            expanded_html.append('\n' + '\t'*depth)
        
        expanded_html.append(char)

    return "".join(expanded_html).strip()


Style: TypeAlias = dict[str,dict[str,str]]

def parse_css(data: str) -> Style:
    """
    Naive css parser
    Returns a dict from selector to a dict of rules to values
    """
    stylesheet = {}
    i0 = 0
    i1 = 0
    current_selectors = []

    while i1 < len(data):
        if data[i1] == '{': # Parse selector
            current_selectors = []
            for selector in data[i0:i1].split(','):
                selector = selector.strip()
                current_selectors.append(selector)
                assert(not selector in stylesheet)
                stylesheet[selector] = {}
            i0 = i1 + 1

        elif data[i1] == '}': # Parse rules
            assert(len(current_selectors) > 0)
            for rule in data[i0:i1].split(';'):
                rule = rule.split(':')
                assert(len(rule) == 2)
                for selector in current_selectors:
                    stylesheet[selector][rule[0]] = rule[1]
            i0 = i1 + 1

        i1 += 1
    
    return stylesheet


class LatinDictHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()

        # list of `(tag, attrs)`
        self.current_tags: list[str, list[tuple[str,str|None]]] = []
        self.style = None

        # list of `(header name, depth)` where `headers[n][1]` means that the header `n+1` has a depth (in `current_tags`) of `headers[n][1]`
        self.headers: list[tuple[str, int]] = []

    def handle_starttag(self, tag, attrs):
        # print("st", tag, attrs)
        self.current_tags.append((tag, attrs,))

        # Handle headers
        if len(tag) == 2 and tag[0] == 'h' and tag[1] in "123456789":
            header_num = int(tag[1])
            if len(self.headers) >= header_num:
                self.headers = self.headers[:header_num-1]
            self.headers.append(('', len(self.current_tags)-1,))
            print(self.headers)

    def handle_endtag(self, tag):
        # print("et", tag)
        if tag != self.current_tags[-1][0]:
            if self.current_tags[-1][0] != "meta":
                raise ValueError("Endtag does not match starttag")

            del self.current_tags[-1]

        del self.current_tags[-1]

    def handle_data(self, data):
        # print("d", data)
        if self.current_tags[-1][0] == "style":
            if not ("type", "text/css") in self.current_tags[-1][1]:
                raise ValueError(f"Cannot parse style with non text/css type: {self.current_tags[-1][1]}")
            self.style = parse_css(data)
        
        # All the vocab we care about is after headers
        if len(self.headers) > 0 and len(self.current_tags) >= 2:
            # Handle header text
            if self.current_tags[-2][0] == 'h' + str(len(self.headers)) and self.current_tags[-1][0] == "span":
                self.headers[-1] = (self.headers[-1][0] + data.replace('\xa0', ' '), self.headers[-1][1],)
                print(self.headers)

            # Numerals are a special case
            if self.headers[-1][0] == "Numerals":
                pass


class HTMLTag:
    def __init__(self, tag: str, attrs: list[tuple[str,str|None]], contains: list[HTMLTag|str], parent: HTMLTag|None = None):
        self.tag = tag
        self.attrs = attrs
        self.contains = contains
        self.parent = parent
    
    def __repr__(self) -> str:
        return f"HTMLTag({self.tag}, {self.attrs}, ..., ...)"
    
    def pretty_print(self, depth=0) -> str:
        pretty_attrs = ' '.join(attr[0] + ("=\"" + attr[1] + '\"' if attr[1] is not None else '') for attr in self.attrs)
        begin = f"<{self.tag} {pretty_attrs}>"
        end = f"</{self.tag}>\n"

        if len(self.contains) == 0:
            return '\t'*depth + begin + end
        
        result = '\t'*depth + begin + '\n'
        for c in self.contains:
            if isinstance(c, HTMLTag):
                result += c.pretty_print(depth+1)
            else:
                result += '\t'*(depth+1) + c + '\n'
        result += '\t'*depth + end
        
        return result
    
    def find(self, tag: str) -> HTMLTag | None:
        """
        Returns first `HTMLTag` in hierarchy (depth first) with tag matching input tag
        """

        if self.tag == tag:
            return self
        for c in self.contains:
            if isinstance(c, HTMLTag):
                if (found := c.find(tag)) is not None:
                    return found
        return None
    
    def flattened_data(self, add_to:list[tuple[str, HTMLTag]]|None = None) -> list[tuple[str, HTMLTag]]:
        """
        Returns data of every HTMLTag in hierarchy in a tuple with the HTMLTag from which it comes (depth first)
        """
        if add_to is None:
            add_to = []

        for c in self.contains:
            if isinstance(c, HTMLTag):
                c.flattened_data(add_to)
            else:
                add_to.append((c, self,))

        return add_to

    def get_attrs(self, filter:str|None = None, split:str|None = None, add_to:list[tuple[str,str]]|list[str]|None = None) -> list[tuple[str,str]] | list[str]:
        """
        Returns `attr`s of `self` and its parents. Attributes of `self` will be first, and each
        subsequent parent will be later in the list

        If `filter` is not `None` returns a `list[str]` of only attributes matching `filter`
        Otherwise returns a `list[tuple[str,str]]` of attributes and their value

        If `split` is not `None` the values of the attrs will be split on `split` before being returned
        """
        if add_to == None:
            add_to = []
        
        if filter is None:
            if split is None:
                add_to += self.attrs
            else:
                for attr, val in self.attrs:
                    for v in val.split(split):
                        add_to.append((attr, v,))
        else:
            for attr, val in self.attrs:
                if attr == filter:
                    if split is None:
                        add_to.append(val)
                    else:
                        add_to += val.split(split)
        
        if self.parent is not None:
            self.parent.get_attrs(filter=filter, split=split, add_to=add_to)

        return add_to


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()

        self.root: HTMLTag|None = None
        self.current: HTMLTag|None = None

    def handle_starttag(self, tag, attrs):
        if tag == "meta": # Ignore the meta tag (it doesn't have a matching closing tag)
            return

        new_tag = HTMLTag(tag, attrs, [])

        if self.current == None:
            assert(tag == "html" and self.root == None)
            self.root = new_tag
        else:
            self.current.contains.append(new_tag)
            new_tag.parent = self.current
        
        self.current = new_tag

    def handle_endtag(self, tag):
        assert(tag == self.current.tag)
        self.current = self.current.parent

    def handle_data(self, data):
        self.current.contains.append(data)


class HTMLReader:
    def __init__(self, parsed_html):
        self.parsed_html = parsed_html

        self.style = parsed_html.find("style")
        assert(len(self.style.contains) == 1 and not isinstance(self.style.contains[0], HTMLTag))
        self.style = parse_css(self.style.contains[0])

        self.vocab_container: HTMLTag|None = None

    def read_html(self):
        resulting_vocab = {}

        self.vocab_container = self.parsed_html.find("h1").parent

        # list of header names where `current_header[n]` represehts the header `n+1`
        # (ie. h1 would be at n=0, h2 would be at n=2, etc.)
        current_headers: list[str|None] = []

        for html_tag in self.vocab_container.contains:
            if not isinstance(html_tag, HTMLTag):
                continue

            # Get the header
            if len(html_tag.tag) == 2 and html_tag.tag[0] == 'h' and html_tag.tag[1] in "123456789":
                header_depth = int(html_tag.tag[1])
                if len(current_headers) >= header_depth:
                    current_headers = current_headers[:header_depth-1]

                elif len(current_headers) < header_depth - 1:
                    current_headers += [None] * (header_depth - 1 - len(current_headers))
                
                header_name = ""
                for data, data_tag in html_tag.flattened_data():
                    if data_tag.tag == "span":
                        header_name += data.replace('\xa0', ' ') # replace no-break-spaces with regular spaces
                current_headers.append(header_name)
                print(current_headers)

                resulting_vocab[header_name] = []

            # Get the english/latin vocab
            elif len(current_headers) > 0:
                if current_headers[-1] == "Numerals": # Numerals are a special case
                    pass
                else:
                    if html_tag.tag == 'p':
                        vocab_reader = VocabReader(self.style, html_tag)
                        if (vocab := vocab_reader.read_data()) is not None:
                            assert len(current_headers) >= 1 and current_headers[-1] in resulting_vocab
                            resulting_vocab[current_headers[-1]].append(vocab)

        return resulting_vocab


class VocabReader:
    def __init__(self, style: Style, html_tag: HTMLTag):
        self.style = style
        self.html_tag = html_tag
        self.vocab_data = html_tag.flattened_data()
        self.vocab: vocab.Vocab|None = None

        self.debug_parsing_info = None
    
    def is_latin(self, data_block: tuple[str, HTMLTag]) -> bool:
        for tag_class in data_block[1].get_attrs("class", ' '):
            tag_class = '.' + tag_class
            if tag_class not in self.style:
                continue
            if "font-weight" in self.style[tag_class] and self.style[tag_class]["font-weight"] == "700":
                return True
        return False

    def is_definition(self, data_block: tuple[str, HTMLTag]) -> bool:
        for tag_class in data_block[1].get_attrs("class", ' '):
            tag_class = '.' + tag_class
            if tag_class not in self.style:
                continue
            if "font-style" in self.style[tag_class] and self.style[tag_class]["font-style"] == "italic":
                return True
        return False
    
    def find_in_data(self, substr: str, word:bool = False, latin:bool|None = None, definition:bool|None = None) -> tuple[int,int]:
        """
        If `substr` is in `self.vocab_data` returns a tuple of two indexes `[i,j]` giving the
        location of `substr` in `self.vocab_data` (ie. `self.vocab_data[i][0][j:len(substr)] == substr`)

        Will return the first match (lowest `i` then lowest `j`). Returns `(-1,-1)` for no match.

        If `word` is `True`, only returns matches where the `substr` is surrounded by non ascii characters
        
        If `latin` is `False`, only returns matches where `self.vocab_data[i]` is latin and vice versa.

        If `definition` is `False`, only returns matches where `self.vocab_data[i]` is a definition and vice versa.
        """
        for i, (data_chunk, tag,) in enumerate(self.vocab_data):
            if latin is not None:
                if self.is_latin((data_chunk, tag,)) != latin:
                    continue
            
            if definition is not None:
                if self.is_definition((data_chunk, tag,)) != definition:
                    continue

            if (index := data_chunk.find(substr)) != -1:
                if not word or (
                        (index == 0 or data_chunk[index-1] not in string.ascii_letters) and 
                        (index+len(substr) == len(data_chunk) or data_chunk[index+len(substr)] not in string.ascii_letters)):
                    return (i, index,)

        return (-1,-1)
    
    def is_verb(self) -> bool:
        if len(self.vocab_data) == 0:
            return False
        
        if not self.is_latin(self.vocab_data[0]):
            return False

        principal_parts = [part.strip() for part in self.vocab_data[0][0].split(',')]
        if len(principal_parts) in (3,4,):
            if len(principal_parts[1]) > 2 and principal_parts[1][-2:] == "re":
                return True
            if principal_parts[1] in ("posse", "esse",): # Exceptions
                return True
        
        return False

    def is_adverb(self) -> bool:
        return self.find_in_data("adv.", word=True, latin=False) != (-1,-1,)

    def is_noun(self) -> bool:
        # raise NotImplementedError()
        return False

    def is_adjective(self) -> bool:
        # raise NotImplementedError()
        return False

    def is_pronoun(self) -> bool:
        return self.find_in_data("pron.", word=True, latin=False) != (-1,-1,)

    def is_preoposition(self) -> bool:
        return self.find_in_data("prep.", word=True, latin=False) != (-1,-1,)

    def is_conjunction(self) -> bool:
        return self.find_in_data("conj.", word=True, latin=False) != (-1,-1,)

    def is_interjection(self) -> bool:
        return self.find_in_data("interj.", word=True, latin=False) != (-1,-1,)

    def determine_vocab_type(self):
        funcs = [
            self.is_verb, 
            self.is_adverb, 
            self.is_noun, 
            self.is_adjective, 
            self.is_pronoun, 
            self.is_preoposition, 
            self.is_conjunction, 
            self.is_interjection]
        
        vocab_type: list[vocab.VocabType] = []

        for potential_vocab_type in vocab.VocabType:
            if funcs[potential_vocab_type.value]():
                vocab_type.append(potential_vocab_type)
        return vocab_type

    def convert_to_vocab_verb(self) -> vocab.Verb:
        principal_parts = [part.strip() for part in self.vocab_data[0][0].split(',')]
        if len(principal_parts) == "3":
            principal_parts.append("")
        principal_parts = tuple(principal_parts)
        verb = vocab.Verb(principal_parts, '')

        if len(self.vocab_data) == 3 and self.vocab_data[1][0] == ", " and self.is_definition(self.vocab_data[2]):
            assert self.vocab_data[2][0][:3] == "to "
            verb.english = self.vocab_data[2][0]
        else:
            for data, tag in self.vocab_data:
                if self.is_definition((data, tag,)):
                    if data[:3] == "to ":
                        verb.english = data

            print(self.debug_parsing_info)
            print(verb)

            # Deal with irregulars
            (i,j,) = self.find_in_data("imp.", word=True, latin=False, definition=False)
            if (i,j,) != (-1,-1,):
                if "sg." in self.vocab_data[i][0][j:]:
                    logging.warning(f"Irregular case unhandled: {self.debug_parsing_info}")
                else:
                    logging.warning(f"Potential irregular case unhandled: {self.debug_parsing_info}")
        
        verb.load()
        return verb

    def convert_to_vocab_adverb(self) -> vocab.Adverb:
        raise NotImplementedError()

    def convert_to_vocab_noun(self) -> vocab.Noun:
        raise NotImplementedError()

    def convert_to_vocab_adjective(self) -> vocab.Adjective:
        raise NotImplementedError()

    def convert_to_vocab_pronoun(self) -> vocab.Pronoun:
        raise NotImplementedError()

    def convert_to_vocab_preoposition(self) -> vocab.Preoposition:
        raise NotImplementedError()

    def convert_to_vocab_conjunction(self) -> vocab.Conjunction:
        raise NotImplementedError()

    def convert_to_vocab_interjection(self) -> vocab.Interjection:
        raise NotImplementedError()

    def read_data(self) -> vocab.Vocab | None:
        vocab_type = []

        toprint = []
        for d in self.vocab_data:
            isgender = False

            if " m." in d[0] or " f." in d[0] or " n." in d[0]:
                isgender = True

            parsed_data = d[0]
            if self.is_latin(d):
                parsed_data = PCol.CRED + parsed_data + PCol.CEND
            if self.is_definition(d):
                parsed_data = PCol.CBLUE + parsed_data + PCol.CEND
            if isgender:
                parsed_data = PCol.CYELLOW + parsed_data + PCol.CEND

            toprint.append(parsed_data)
        
        vocab_type = self.determine_vocab_type()
        prelude = ""
        if vocab.VocabType.Verb in vocab_type:
            prelude += PCol.CVIOLET + "[verb]" + PCol.CEND + ' '
        if vocab.VocabType.Adverb in vocab_type:
            prelude += PCol.CVIOLET + "[adv.]" + PCol.CEND + ' '
        if vocab.VocabType.Noun in vocab_type:
            prelude += PCol.CVIOLET + "[noun]" + PCol.CEND + ' '
        if vocab.VocabType.Adjective in vocab_type:
            prelude += PCol.CVIOLET + "[adj.]" + PCol.CEND + ' '
        if vocab.VocabType.Pronoun in vocab_type:
            prelude += PCol.CVIOLET + "[pron.]" + PCol.CEND + ' '
        if vocab.VocabType.Preposition in vocab_type:
            prelude += PCol.CVIOLET + "[prep.]" + PCol.CEND + ' '
        if vocab.VocabType.Conjunction in vocab_type:
            prelude += PCol.CVIOLET + "[conj.]" + PCol.CEND + ' '
        if vocab.VocabType.Interjection in vocab_type:
            prelude += PCol.CVIOLET + "[interj.]" + PCol.CEND + ' '

        self.debug_parsing_info = prelude + f"{PCol.CGREY}|{PCol.CEND}".join(p for p in toprint)
        
        if len(vocab_type) == 1:
            funcs = [
                self.convert_to_vocab_verb, 
                self.convert_to_vocab_adverb, 
                self.convert_to_vocab_noun, 
                self.convert_to_vocab_adjective, 
                self.convert_to_vocab_pronoun, 
                self.convert_to_vocab_preoposition, 
                self.convert_to_vocab_conjunction, 
                self.convert_to_vocab_interjection]
            try:
                self.vocab = funcs[vocab_type[0].value]()
            except NotImplementedError:
                pass
        
        if self.vocab is not None:
            self.vocab.description = self.debug_parsing_info
        
        return self.vocab


if __name__ == "__main__":
    parsed_html: HTMLTag|None = None

    with open("LatinDictionary.html", 'r') as f:
        parser = MyHTMLParser()
        parser.feed(f.readline())
        parser.close()
        parsed_html = parser.root
    
    html_reader = HTMLReader(parsed_html)
    parsed_vocab = html_reader.read_html()

    import visualizer
    vis = visualizer.Visualizer()
    vis.vocab = parsed_vocab
    vis.visualize()

    if False:
        expanded_html = None
        with open("LatinDictionary.html", 'r') as f:
            expanded_html = expand_html(f.readline())
        
        with open("ExpandedLatinDictionary.html", 'w') as f:
            f.write(expanded_html)


