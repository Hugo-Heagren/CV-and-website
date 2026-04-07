.DELETE_ON_ERROR:
SHELL=/bin/bash

# Definitions
export OUT_DIR=/tmp/site/
export INFO_JSON_FILE=./info.json
export BIB_XML_FILE=./cv.bltxml
export CV_BIB_FILE=./cv.bib
export CV_BCF_FILE=./cv.bcf
export CV_BBL_FILE=./cv.bbl
export CV_TEX_FILE=./cv.tex
export BIBER_TOOL_CONF_FILE=./biber-tool.conf
export LATEX=lualatex

${CV_BCF_FILE}:
	${LATEX} ${CV_TEX_FILE}

${CV_BBL_FILE}: ${CV_BCF_FILE}
	biber cv

${BIBER_TOOL_CONF_FILE}: ${CV_BCF_FILE}
	${PYTHON} ./generate-biber-datamodel.py \
		${CV_BCF_FILE} \
		${BIBER_TOOL_CONF_FILE}

${BIB_XML_FILE}: ${CV_BIB_FILE} ${BIBER_TOOL_CONF_FILE}
	biber --tool \
		--configfile ${BIBER_TOOL_CONF_FILE} \
		--output-format=biblatexml \
		--output-file=${BIB_XML_FILE} \
		${CV_BIB_FILE}

${OUT_DIR}:
	# "--parents" will create parent directories if needed
	mkdir --parents ${OUT_DIR}

.PHONY: site
site: ${BIB_XML_FILE} ${INFO_JSON_FILE} ${OUT_DIR}
	${PYTHON} ./site/build.py ${OUT_DIR} ${BIB_XML_FILE} ${INFO_JSON_FILE}

${CV_TEX_FILE}: ${CV_BBL_FILE} cv.bbx cv.dbx
	${LATEX} ${CV_TEX_FILE}
	${LATEX} ${CV_TEX_FILE}


.PHONY: cv
cv: ${CV_TEX_FILE}

export PUB_LIST=./list-of-publications
export PUB_LIST_TEX_FILE=${PUB_LIST}.tex
export PUB_LIST_BCF_FILE=${PUB_LIST}.bcf
export PUB_LIST_BBL_FILE=${PUB_LIST}.bbl

${PUB_LIST_BCF_FILE}: ${CV_BIB_FILE}
	${LATEX} ${PUB_LIST_TEX_FILE}

${PUB_LIST_BBL_FILE}: ${PUB_LIST_BCF_FILE}
	biber ${PUB_LIST}

# TODO variables for cv.{bbx,dbx}
${PUB_LIST_TEX_FILE}: ${PUB_LIST_BBL_FILE} cv.bbx cv.dbx
	 ${LATEX} ${PUB_LIST_TEX_FILE}
	 ${LATEX} ${PUB_LIST_TEX_FILE}

.PHONY: pub-list
pub-list: ${PUB_LIST_TEX_FILE}

.PHONY: referees
referees:
	${LATEX} referees.tex

.PHONY: clean
clean:
	rm -rf ${OUT_DIR} ${BIB_XML_FILE} ${CV_BCF_FILE} ${BIBER_TOOL_CONF_FILE} \
		*.{aux,bbl,bcf,blg,bltxml,dvi,fdb_latexmk,fls,log,out,pdf,rng,run.xml,synctex.gz}

