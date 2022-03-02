all: fse22-brepair.pdf

%.pdf: %.tex %.bib
	latexmk -pdf $*.tex

submission:
	$(MAKE) clean
	touch SUBMIT
	$(MAKE)
	rm SUBMIT

clean:
	latexmk -C
