from jinja2 import Environment, FileSystemLoader, meta
from pathlib import Path 
import os
import glob
from shutil import copytree
from sitemap import Url, Urlset
from urllib.parse import urljoin
import git
import datetime

# Jinja environment
env = Environment(loader=FileSystemLoader("."))

# * HTML Munging

# Create and populate a dictionary mapping code points to HTML entity
# strings
codepoint_ent_map = {}
# I'm assuming I'll only ever really need the standard ASCII
# characters (i.e. code points 32-126), though this isn't
# technically true: https://www.netmeister.org/blog/email.html
for c in range(32, 126):
    codepoint_ent_map[c] = f'&#{c};'

def html_mung(value):
    return value.translate(codepoint_ent_map)

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


# ** Write sitemap

urls.write_xml(out_dir / 'sitemap.xml')

# ** Copy all the assets

copytree("assets", out_dir / "assets", dirs_exist_ok=True)
