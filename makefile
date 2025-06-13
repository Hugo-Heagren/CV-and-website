.DELETE_ON_ERROR:

# Definitions
OUT_DIR := /tmp/site/
BIB_XML_FILE := cv.bltxml
INFO_JSON_FILE := ./info.json
CV_BCF_FILE := ./cv.bcf
BIBER_TOOL_CONF_FILE := ./biber-tool.conf
PYTHON := ./venv/bin/python3

# Remember how make works -- this is only run if we need a .bcf file,
# and there isn't already an up-to-date-enough one.
${CV_BCF_FILE}:
	lualatex cv.tex
	biber cv

${BIBER_TOOL_CONF_FILE}: ${CV_BCF_FILE}
	 ${PYTHON} ./generate-biber-datamodel.py \
		${CV_BCF_FILE} \
		${BIBER_TOOL_CONF_FILE}

${BIB_XML_FILE}: cv.bib ${BIBER_TOOL_CONF_FILE}
	biber --tool \
		--configfile ${BIBER_TOOL_CONF_FILE} \
		--output-format=biblatexml \
		--output-file=${BIB_XML_FILE} \
		cv.bib

site: ${BIB_XML_FILE} ${INFO_JSON_FILE}
	${PYTHON} build.py ${OUT_DIR} ${BIB_XML_FILE} ${INFO_JSON_FILE}
