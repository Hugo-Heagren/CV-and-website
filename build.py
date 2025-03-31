from jinja2 import Environment, FileSystemLoader, meta
from pathlib import Path 
import os
import glob
from shutil import copytree
from sitemap import Url, Urlset
from urllib.parse import urljoin
import git
import datetime
import unicodedata
import argparse
from lxml import etree
from edtf import parse_edtf

# * Arguments

arg_parser = argparse.ArgumentParser()

class PathAction(argparse.Action):
    """
    Action for storing a string argument as a Path object.
    """
    def __init__ (self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, Path(values))


arg_parser.add_argument("out_dir",
                        help="Output directory for site artifacts",
                        action=PathAction)

# Parse the args!
args = arg_parser.parse_args()

# * Jinja environment

env = Environment(loader=FileSystemLoader("."))

# * Research data
# ** BibLaTeX data parser

bib_date_components = {'day', 'month', 'year', 'hour', 'minute', 'second', 'timezone'}

class BibEntry(dict):
    def __getitem__(self, key):
        # TODO Use python-edtf to support partial dates...
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
        self.date_type = None
        self.namepart_type = None
    def start(self, tag, attrib):
        tag_name = etree.QName(tag).localname
        # TODO use pattern matching here?
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
        elif tag_name == 'namepart':
            self.namepart_type = attrib.get("type")
        elif tag_name == 'date' and attrib.get("type", False):
            # If there's a type, use that
            type = attrib.get("type")
            self.date_type = type
            self.current_field.append(f"{type}date")
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
        # Reset the namepart/date type tracker when necessary
        if tag_name == 'namepart':
            self.namepart_type = None
        elif tag_name == 'date':
            self.date_type = None
    def data(self, data):
        # Handle dates
        if self.namepart_type is not None:
            # This is only true when we're in a namepart tag
            field = 'namepart'
        else:
            field = self.current_field[-1]
        match field:
            case 'entries':
                pass
            case 'date':
                str = data.strip()
                # String date (not a range)
                if str != '':
                    date = iso.parse_date(str)
                    # Account for other kinds of date
                    tag = f"{self.date_type or ''}date"
                    self.current_entry[tag] = date
                    # Otherwise we're in a range, so do nothing yet
            # Date ranges...
            case 'start':
                str = data.strip()
                start_date = iso.parse_date(str)
                tag = f"{self.date_type or ''}date"
                self.current_entry[tag] = DateRange()
                self.current_entry[tag].start = start_date
            case 'end':
                str = data.strip()
                end_date = iso.parse_date(str)
                tag = f"{self.date_type or ''}date"
                self.current_entry[tag].end = end_date
            case 'list':
                pass
            case 'item':
                list_field = self.current_field[-2]
                self.current_entry[list_field].append(data)
            case 'names':
                pass
            case 'name':
                pass
            case 'namepart':
                str = data.strip()
                namelist_field = self.current_field[-1]
                setattr(self.current_entry[namelist_field][-1], self.namepart_type, str)
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

# ** Get the data

biblatex_parser = etree.XMLParser(target=BibLateXMLParser(),
                                  remove_blank_text=True)

# TODO This makes the file a magic string!
# Parse the data into the environment
env.globals['research'] = etree.parse("/home/hugo/site/cv_bibertool.bltxml",
                                      biblatex_parser)

# ** Jinja filters

def bib_filter(entry, **kwargs):
    if len(kwargs) != 1:
        raise ValueError("Bibfilter needs exactly one key=value pair")
    field, test = next(iter(kwargs.items()))
    if entry[field] == test:
        return True
    else:
        return False

env.tests["bibfilter"] = bib_filter

# * HTML Munging

# https://dr0.ch/email-munging/
class HTMLMunger:
    """
    Functional map for getting HTML entity strings.
    """

    # `c' is a unicode point -- i.e. an int
    def __getitem__(self, c: int):
        # Only allow for valid unicode characters.
        # Attribution: https://stackoverflow.com/a/69780841
        if (unicodedata.category(chr(c)) not in ('Cn', 'Cs', 'Co')):
            return f'&#{c};'
        else:
            raise IndexError(f"""{c} is not a valid unicode code
            point, and thus cannot be translated""")

def html_mung(value):
    return value.translate(HTMLMunger())

# Make available
env.filters["html_mung"] = html_mung

# * Setup for sitemap

# Variables for sitemap stuff
urls = Urlset()
domain = "https://hugoheagren.com"

repo = git.Repo()
tree = repo.heads.master.commit.tree
def get_git_mod_time(file):
    gen = repo.iter_commits(paths=tree[file].path, max_count=1)
    commit = next(gen)
    return commit.committed_date

# * Build

# Define output dir and make sure it exists
out_dir = args.out_dir
out_dir.mkdir(parents=True, exist_ok=True)

# I don't really need template expansion in my CSS file, but it's
# there if I ever do, and this makes the build script simpler.
files = glob.glob(r'*.html') + glob.glob(r'*.css')

for file in files:
    # Render the file
    filename = out_dir / file
    template = env.get_template(file)
    content = template.render()
    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(content)

    # Populate times for sitemap (doing this here so I don't have to
    # go loop over the files twice)
    with open(file, mode="r", encoding="utf-8") as input:
        # NOTE This is simple, and it works because I don't use templates
        # which inherit from each other. If I ever do, I'll need to build a
        # full-on dependency graph, recursively populate their dependencies on
        # each other.
        ast = env.parse(input.read())
        input.close()
        templates = list(meta.find_referenced_templates(ast))
        times = []
        for t in list(map(get_git_mod_time, [file, *templates])):
            times.append(t)
        time = datetime.datetime.fromtimestamp(max(times))

        # Populate metadata for sitemap
        url = Url(urljoin(domain, file), lastmod=time)
        urls.add_url(url)


# ** Write sitemap and robots.txt

sitemap_name = 'sitemap.xml'

urls.write_xml(out_dir / sitemap_name)

# Declare sitemap in robots.txt
with open(out_dir / 'robots.txt', "w") as robots:
    robots.write(f"sitemap: {urljoin(domain, sitemap_name)}")

# ** Copy all the assets

copytree("assets", out_dir / "assets", dirs_exist_ok=True)
