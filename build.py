from jinja2 import Environment, FileSystemLoader, meta
from pathlib import Path
import glob
from shutil import copytree
from sitemap import Url, Urlset
from urllib.parse import urljoin
import git
import datetime  # For lastmod times in sitemap URLs
import unicodedata
import argparse
from lxml import etree
from edtf import parse_edtf, Interval, EDTFObject
import rcssmin
import json

# * Arguments

arg_parser = argparse.ArgumentParser()


class PathAction(argparse.Action):
    """
    Action for storing a string argument as a Path object.
    """

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, Path(values))


arg_parser.add_argument(
    "out_dir", help="Output directory for site artifacts", action=PathAction
)

arg_parser.add_argument("bib_xml_file", help="BibLaTeXML file with bibliography data")

arg_parser.add_argument(
    "info_json_file", help="JSON file containing general information on me"
)

# Parse the args!
args = arg_parser.parse_args()

# * Jinja environment

env = Environment(loader=FileSystemLoader("."))

# Load general info into the global environment
with open(args.info_json_file) as f:
    env.globals["info"] = json.load(f)

# * Research data
# ** BibLaTeX data parser

bib_date_components = {"day", "month", "year", "hour", "minute", "second", "timezone"}


class BibEntry(dict):
    def __getitem__(self, key):
        if key in bib_date_components:
            date = self.get("date")
            # This isn't strictly right, but it'll do fine until I
            # need to handle time properly (i.e. if I ever give two
            # separate talks on one day...)
            if isinstance(date, EDTFObject):
                return getattr(date, key)
            else:
                raise KeyError(
                    f"Cannot get '{key}' because 'date' is not set or is not an EDTFObject"
                )
        # Fallback to standard dict behaviour
        else:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key in bib_date_components:
            raise KeyError(
                f"Cannot set '{key}' because 'date' is not set or is not an EDTFObject"
            )
        # Fallback to standard dict behaviour
        else:
            super().__setitem__(key, value)

    # This is handy for jinja
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            )


class BibName:
    def __init__(self, prefix=None, given=None, family=None, suffix=None):
        self.prefix = prefix
        self.given = given
        self.family = family
        self.suffix = suffix

    def __repr__(self):
        return (
            f"BibName(p={self.prefix} g={self.given} f={self.family} s={self.suffix})"
        )


class PageRange:
    def __init__(self, lower=None, upper=None):
        self.lower = lower
        self.upper = upper


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
            self.current_entry = BibEntry()
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
            self.current_entry[self.current_field].append(BibName())
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
                        PageRange(lower=string)
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


# ** Get the data

biblatex_parser = etree.XMLParser(target=BibLateXMLParser(), remove_blank_text=True)

# Parse the data into the environment
bib_xml_file = args.bib_xml_file
env.globals["research"] = etree.parse(bib_xml_file, biblatex_parser)

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
        if unicodedata.category(chr(c)) not in ("Cn", "Cs", "Co"):
            return f"&#{c};"
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
tree = repo.active_branch.commit.tree


def get_git_mod_time(file):
    gen = repo.iter_commits(paths=tree[file].path, max_count=1)
    commit = next(gen)
    return commit.committed_date


# * Build

# Define output dir and make sure it exists
out_dir = args.out_dir
out_dir.mkdir(parents=True, exist_ok=True)

html_files = glob.glob(r"*.html")

for file in html_files:
    # render the file
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


# Minify CSS
css_files = glob.glob(r"*.css")
for file in css_files:
    with open(file, mode="r", encoding="utf-8") as input:
        original_css = input.read()
        minified_css = rcssmin.cssmin(original_css)
        input.close()
        output_path = out_dir / file
        with open(output_path, mode="w", encoding="utf-8") as output:
            output.write(minified_css)

# ** Write sitemap and robots.txt

sitemap_name = "sitemap.xml"

urls.write_xml(out_dir / sitemap_name)

# Declare sitemap in robots.txt
with open(out_dir / "robots.txt", "w") as robots:
    robots.write(f"sitemap: {urljoin(domain, sitemap_name)}")

# ** Copy all the assets

copytree("assets", out_dir / "assets", dirs_exist_ok=True)
