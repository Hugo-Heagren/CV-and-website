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

# Jinja environment
env = Environment(loader=FileSystemLoader("."))

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
            raise IndexError(f"""{123} is not a valid unicode code
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
out_dir = Path("/tmp/site")
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
