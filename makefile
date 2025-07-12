.DELETE_ON_ERROR:
SHELL=/bin/bash

${CV_BCF_FILE}:
	${LATEX} cv.tex

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

.PHONY: cv
cv: ${CV_BBL_FILE}
	${LATEX} cv.tex
	${LATEX} cv.tex

.PHONY: clean
clean:
	rm -rf ${OUT_DIR} ${BIB_XML_FILE} ${CV_BCF_FILE} ${BIBER_TOOL_CONF_FILE} \
		*.{aux,bbl,bcf,blg,bltxml,dvi,fdb_latexmk,fls,log,out,pdf,rng,run.xml,synctex.gz}

