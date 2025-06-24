from jinja2 import Environment, FileSystemLoader, meta
from pathlib import Path
from shutil import copytree
from sitemap import Url, Urlset
from urllib.parse import urljoin
import git
import datetime  # For lastmod times in sitemap URLs
import unicodedata
import argparse
from lxml import etree
import rcssmin
import json
from lib import bib_parser as bp

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

# * Useful variables (git, dirs, etc.)

repo = git.Repo()
tree = repo.active_branch.commit.tree

repo_dir = Path(repo.common_dir).parent

site_dir = repo_dir / "site"

# * Jinja environment

env = Environment(
    loader=FileSystemLoader(site_dir), trim_blocks=True, lstrip_blocks=True
)

# * Environment data
# ** General info

# Load general info into the global environment
with open(args.info_json_file) as f:
    env.globals["info"] = json.load(f)

# ** Eval data schema

# This is useful for getting the shortnames of columns, or filtering
# columns by type, etc. in jinja templates.
with open(repo_dir / "teaching-evals/schema.json") as f:
    env.globals["eval_schema"] = json.load(f)

# ** Bibliography data

biblatex_parser = etree.XMLParser(target=bp.BibLateXMLParser(), remove_blank_text=True)

# Parse the data into the environment
bib_xml_file = args.bib_xml_file
env.globals["research"] = etree.parse(bib_xml_file, biblatex_parser)

# * Jinja filters
# ** Bib data


def bib_filter(entry, **kwargs):
    if len(kwargs) != 1:
        raise ValueError("Bibfilter needs exactly one key=value pair")
    field, test = next(iter(kwargs.items()))
    if entry[field] == test:
        return True
    else:
        return False


env.tests["bibfilter"] = bib_filter

# ** HTML Munging


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


def get_git_mod_time(file):
    relative_file = Path(file).relative_to(repo_dir)
    gen = repo.iter_commits(paths=tree[str(relative_file)].path, max_count=1)
    commit = next(gen)
    return commit.committed_date


# * Build

# Define output dir and make sure it exists
out_dir = args.out_dir
out_dir.mkdir(parents=True, exist_ok=True)

template_dir = site_dir / "pages"

template_files = template_dir.glob("*.html")

for file in template_files:
    # render the file
    out_file = out_dir / file.relative_to(template_dir)
    template = env.get_template(str(file.relative_to(env.loader.searchpath[0])))
    content = template.render()
    with open(out_file, mode="w", encoding="utf-8") as output:
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
        template_rel_paths = list(meta.find_referenced_templates(ast))
        template_abs_paths = [str(site_dir / f) for f in template_rel_paths]
        times = []
        for t in list(map(get_git_mod_time, [file, *template_abs_paths])):
            times.append(t)
        time = datetime.datetime.fromtimestamp(max(times))

        # Populate metadata for sitemap
        url = Url(urljoin(domain, str(file)), lastmod=time)
        urls.add_url(url)


# Minify CSS
css_files = site_dir.glob("*.css")
for file in css_files:
    with open(file, mode="r", encoding="utf-8") as input:
        original_css = input.read()
        minified_css = rcssmin.cssmin(original_css)
        input.close()
        output_path = out_dir / file.relative_to(site_dir)
        with open(output_path, mode="w", encoding="utf-8") as output:
            output.write(minified_css)

# ** Write sitemap and robots.txt

sitemap_name = "sitemap.xml"

urls.write_xml(out_dir / sitemap_name)

# Declare sitemap in robots.txt
with open(out_dir / "robots.txt", "w") as robots:
    robots.write(f"sitemap: {urljoin(domain, sitemap_name)}")

# ** Copy all the assets

copytree(repo_dir / "assets", out_dir / "assets", dirs_exist_ok=True)
