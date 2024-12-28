from jinja2 import Environment, FileSystemLoader
from pathlib import Path 
import os
import glob
from shutil import copytree

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

# * Build

# Define output dir and make sure it exists
out_dir = Path("/tmp/site")
out_dir.mkdir(parents=True, exist_ok=True)

# I don't really need template expansion in my CSS file, but it's
# there if I ever do, and this makes the build script simpler.
files = glob.glob(r'*.html') + glob.glob(r'*.css')

for file in files:
    filename = out_dir / file
    template = env.get_template(file)
    content = template.render()

    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(content)

# Copy all the assets
# should be a way of not doing that.
copytree("assets", out_dir / "assets", dirs_exist_ok=True)
