all: fse22-brepair.pdf

%.pdf: %.tex %.bib
	latexmk -pdf $*.tex

clean:
	latexmk -C
