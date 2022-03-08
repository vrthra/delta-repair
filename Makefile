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

pull:
	git pull --rebase origin main --autostash

push:
	git push origin main

testbrepair:

	python3 brepair.py '{ "ABCD":[*"1,2,3,4,5,6"]*}'  | grep FIX
	python3 brepair.py '{ "item": "Apple", "price": ***3.45 }'  | grep FIX
	python3 brepair.py '[**]'  | grep FIX
	python3 brepair.py '[**1]'  | grep FIX
	python3 brepair.py '[*1*]'  | grep FIX
	python3 brepair.py '{ "name": "Dave" "age": 42 }'  | grep FIX
