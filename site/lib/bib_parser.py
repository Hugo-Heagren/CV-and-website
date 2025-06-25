from lxml import etree
from edtf import parse_edtf, Interval
from lib import bib_data as bd

data_structure_fields = {
    "list",
    "names",
    "name",
    "namepart",
    "item",
    "entry",
    "entries",
    "start",
    "end",
}


class BibLateXMLParser:
    def __init__(self):
        self.entries = []
        self.current_field = None
        self.current_entry = None
        # For tracking which part of a name we are recording
        self.namepart_type = None
        # Accumulating data
        # https://stackoverflow.com/a/79547360/14915848
        self.current_data = ""

    def start(self, tag, attrib):
        tag_name = etree.QName(tag).localname
        if tag_name == "entry":
            self.current_entry = bd.BibEntry()
            # Default to `misc'
            self.current_entry["type"] = attrib.get("entrytype", "misc")
            self.current_entry["id"] = attrib.get("id")
        elif tag_name == "list":
            self.current_entry[self.current_field] = []
        elif tag_name == "names":
            # List of names
            name_field = attrib.get("type")
            self.current_field = name_field
            self.current_entry[name_field] = []
        elif tag_name == "name":
            # Fairly sure names only ever occur as part of namelists.
            self.current_entry[self.current_field].append(bd.BibName())
        elif tag_name == "namepart":
            self.namepart_type = attrib.get("type")
        elif tag_name == "date" and attrib.get("type", False):
            # If there's a type, use that
            type = attrib.get("type")
            self.current_field = f"{type}date"
        elif tag_name not in data_structure_fields:
            self.current_field = tag_name

    def end(self, tag):
        tag_name = etree.QName(tag).localname
        string = self.current_data.strip()
        match tag_name:
            case "entry":
                if self.current_entry is not None:
                    self.entries.append(self.current_entry)
                    self.current_entry = None
            case "date":
                date = None
                # String date
                if string != "":
                    date = parse_edtf(string)
                    self.current_entry[self.current_field] = date
                    # Otherwise a range, handled already by
                    # start/end...
            # Date ranges
            case "start":
                if self.current_field.endswith("date"):
                    if string == "":
                        # Special case to cope with open intervals
                        start_date = None
                    else:
                        start_date = parse_edtf(string)
                    self.current_entry[self.current_field] = Interval(
                        lower=start_date, upper=None
                    )
                elif self.current_field == "pages":
                    self.current_entry[self.current_field].append(
                        bd.PageRange(lower=string)
                    )
            case "end":
                if self.current_field.endswith("date"):
                    if string == "":
                        # Special case to cope with open intervals
                        end_date = None
                    else:
                        end_date = parse_edtf(string)
                    self.current_entry[self.current_field].upper = end_date
                elif self.current_field == "pages":
                    self.current_entry[self.current_field][-1].upper = string
            case "item":
                list_field = self.current_field
                self.current_entry[list_field].append(string)
            case "namepart":
                namelist_field = self.current_field
                setattr(
                    self.current_entry[namelist_field][-1], self.namepart_type, string
                )
            case _:
                if (
                    self.current_entry is not None
                    and tag_name not in data_structure_fields
                ):
                    # Only write if we haven't written already. This
                    # is because the (entirely whitespace) string
                    # between the end of one end-tag string and the
                    # beginning of the following end-tag is recorded
                    # as 'data, e.g. between these:
                    #   </bltx:date>
                    # </bltx:entry>
                    # In some XML docs, this would be real data, but
                    # it NEVER is in BibLaTeXML, so (luckily!) we can
                    # ignore it, with this test.
                    if not (hasattr(self.current_entry, tag_name)):
                        self.current_entry[tag_name] = string
        # Reset state
        self.current_data = ""
        if tag_name == "namepart":
            self.namepart_type = None

    def data(self, data):
        # Ignore completely empty segments but keep spaces
        if data.strip():
            # Append raw data, preserving spaces
            self.current_data += data

    def close(self):
        # Reset parser
        entries = self.entries
        self.entries = []
        return entries
