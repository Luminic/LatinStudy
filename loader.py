from html.parser import HTMLParser


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

        # if char == '>':
        #     expanded_html.append('\n')

    return "".join(expanded_html)

def parse_css(data: str) -> dict[str, dict[str, str]]:
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

        self.current_tags = []
        self.style = None

    def handle_starttag(self, tag, attrs):
        self.current_tags.append((tag, attrs,))

    def handle_endtag(self, tag):
        if tag != self.current_tags[-1][0]:
            if self.current_tags[-1][0] != "meta":
                raise ValueError("Endtag does not match starttag")

            del self.current_tags[-1]

        del self.current_tags[-1]

    def handle_data(self, data):
        if self.current_tags[-1][0] == "style":
            if not ("type", "text/css") in self.current_tags[-1][1]:
                raise ValueError(f"Cannot parse style with non text/css type: {self.current_tags[-1][1]}")
            self.style = parse_css(data)
        



if __name__ == "__main__":
    expanded_html = None
    with open("LatinDictionary.html", 'r') as f:
        # parser = LatinDictHTMLParser()
        # parser.feed(f.readline())
        # parser.close()

        expanded_html = expand_html(f.readline())
    
    with open("ExpandedLatinDictionary.html", 'w') as f:
        f.write(expanded_html)


