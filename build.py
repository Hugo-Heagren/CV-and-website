from jinja2 import Environment, FileSystemLoader
import glob
from shutil import copytree

output_dir = f"/tmp/site"
env = Environment(loader=FileSystemLoader("."))

# I don't really need template expansion in my CSS file, but it's
# there if I ever do, and this makes the build script simpler.
files = glob.glob(r'*.html') + glob.glob(r'*.css')

for file in files:
    filename = f"/tmp/site/{file}"
    template = env.get_template(file)
    content = template.render()
    with open(filename, mode="w", encoding="utf-8") as output:
        output.write(content)

# Copy all the assets
# TODO This is brittle. I'm making assumptions about slashes. There
# should be a way of not doing that.
copytree("assets", f"{output_dir}/assets", dirs_exist_ok=True)
