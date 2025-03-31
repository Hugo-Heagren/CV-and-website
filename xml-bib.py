from lxml import etree
from datetime import datetime
import isodate as iso

bib_date_components = {'day', 'month', 'year', 'hour', 'minute', 'second', 'timezone'}

class BibEntry(dict):
    def __getitem__(self, key):
        # TODO support other kinds of date (eventdates etc.)
        # Support clever dates
        if key in bib_date_components:
            date = self.get('date')
            if isinstance(date, datetime):
                return getattr(date, key)
            else:
                raise KeyError(f"Cannot get '{key}' because 'date' is not set or is not a datetime object")
        # Fallback to standard dict behaviour
        else:
            return super().__getitem__(key)
    def __setitem__(self, key, value):
        # TODO I'm going to need something here for moving between
        # strings and dates when setting the date slot...
        if key in bib_date_components:
            raise KeyError(f"Cannot set '{key}' because 'date' is not set or is not a datetime object")
        # Fallback to standard dict behaviour
        else:
            super().__setitem__(key, value)
    # This is handy for jinja
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

class DateRange:
    def __init__(self, start=None, end=None):
        if start != None and isinstance(start, datetime):
            self.start = start
        if end != None and isinstance(end, datetime):
            self.end = end
    def __repr__(self):
        return f"DateRange({self.start}, {self.end})"

class BibName:
    def __init__(self, prefix=None, given=None, family=None, suffix=None):
        self.prefix = prefix
        self.given = given
        self.family = family
        self.suffix = suffix
    def __repr__(self):
        return f"BibName(p={self.prefix} g={self.given} f={self.family} s={self.suffix})"

data_structure_fields = {'list', 'names', 'name', 'namepart'}

class BibLateXMLParser:
    def __init__(self):
        self.entries = []
        # Use a stack for the current field
        self.current_field = []
        self.current_entry = None
        self.namepart_type = None
    def start(self, tag, attrib):
        tag_name = etree.QName(tag).localname
        if tag_name == 'entry':
            self.current_entry = BibEntry()
            # Default to `misc'
            self.current_entry["type"] = attrib.get("entrytype", "misc")
            self.current_entry["id"] = attrib.get("id")
        elif tag_name == 'list':
            self.current_entry[self.current_field[-1]] = []
        elif tag_name == 'names':
            # List of names
            name_field = attrib.get("type")
            self.current_field.append(name_field)
            self.current_entry[name_field] = []
        elif tag_name == 'name':
            # Faaaaairly sure names only ever occur as part of
            # namelists?
            self.current_entry[self.current_field[-1]].append(BibName())
        elif tag_name not in data_structure_fields:
            self.current_field.append(tag_name)
    def end(self, tag):
        tag_name = etree.QName(tag).localname
        if tag_name == 'entry' and self.current_entry:
            self.entries.append(self.current_entry)
            self.current_entry = None
        # Leaving a field
        elif tag_name not in data_structure_fields or tag_name == 'names':
            # The 'names' case is because namelist fields appear in
            # the XML as 'names' tags, with a type attrib saying what
            # the actual *field* is, but we record them in the python
            # data structure with that field, not with 'names'
            self.current_field.pop()
    def data(self, data):
        # Handle dates
        # TODO handle other date types
        # TODO Use pattern matching here
        field = self.current_field[-1]
        match field:
            case 'entries':
                pass
            case 'date':
                str = data.strip()
                # String date
                if str != '':
                    date = iso.parse_date(str)
                    self.current_entry['date'] = date
                    # Otherwise we're in a range, so do nothing yet
            # Date ranges...
            case 'start':
                str = data.strip()
                start_date = iso.parse_date(str)
                self.current_entry['date'] = DateRange()
                self.current_entry['date'].start = start_date
            case 'end':
                str = data.strip()
                end_date = iso.parse_date(str)
                self.current_entry['date'].end = end_date
            case 'list':
                pass
            case 'item':
                list_field = self.current_field[-2]
                self.current_entry[list_field].append(data)
            # TODO handle names
            case 'names':
                pass
            case 'name':
                pass
            case _:
                if self.current_entry is not None:
                    # Only write if we haven't written already...
                    if not(hasattr(self.current_entry, field)):
                        self.current_entry[field] = data
    def close(self):
        # Reset parser
        entries = self.entries
        self.entries = []
        return entries

# Then we can parse with something like:
parser = etree.XMLParser(target=BibLateXMLParser(), remove_blank_text=True)
tree = etree.parse("/home/hugo/site/simple.xml", parser)
