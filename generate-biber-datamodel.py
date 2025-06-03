import argparse
from lxml import etree

# * Arguments

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument("cv_bcf_file", help=".bcf file from building CV")

arg_parser.add_argument(
    "biber_tool_conf_filepath", help="filepath for biber toolmode config file."
)

# Parse the args!
args = arg_parser.parse_args()

# * Parse BCF file
bcf_tree = etree.parse(args.cv_bcf_file)

bcf_root = bcf_tree.getroot()

bcf_datamodel = bcf_root.find("{https://sourceforge.net/projects/biblatex}datamodel")

# This is a list of all "entryfields" tags in the bcf file
bcf_all_entryfields = bcf_datamodel.findall(
    "{https://sourceforge.net/projects/biblatex}entryfields"
)

# * Create biber tool config document

# Define a root object...
biber_conf_root = etree.Element("config")

# ...and a tree to wrap it in (tree represents a whole document)
biber_conf_tree = etree.ElementTree(biber_conf_root)

# * Append datamodel (from the bcf) to the biber-tool.conf document

# Here, we just copy the datamodel node from the bcf file into the
# biber conf file (though we strip the namespaces on the way). This
# works because the definition of the datamodel is structured in
# exactly the same way in the two files.

# This is the only node we're interested in. Biber is clever, and will
# fall back to the default config for anything the local file doesn't
# cover.
biber_conf_datamodel = etree.SubElement(biber_conf_root, "datamodel")


def scrub_namespace(elem):
    """
    Recursively remove namespaces from elem and all its children (in place).
    """
    localname = etree.QName(elem.tag).localname
    elem.tag = localname
    for child in elem:
        scrub_namespace(child)


# Iterate over all the entrytype declarations from the bcf, and add
# each one to the biber-tool.conf document
for child in bcf_datamodel:
    scrub_namespace(child)
    biber_conf_datamodel.append(child)

# * Write biber-tool.conf file

biber_conf_tree.write(
    args.biber_tool_conf_filepath,
    xml_declaration=True,
    encoding="UTF-8",
    pretty_print=True,
)
