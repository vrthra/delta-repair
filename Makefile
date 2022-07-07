all: icse23-brepair.pdf

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

PATTERN="Number"

testbrepair:
	python3 brepair.py 'truestory"'  | grep $(PATTERN)
	python3 brepair.py '{"_":a{}}'  | grep $(PATTERN)
	python3 brepair.py '{ "ABCD":[*"1,2,3,4,5,6"]*}'  | grep $(PATTERN)
	python3 brepair.py '{ "item": "Apple", "price": ***3.45 }'  | grep $(PATTERN)
	python3 brepair.py '{ "item": "Apple", "price": **3.45 }'  | grep $(PATTERN)
	python3 brepair.py '[*1, *2]'  | grep $(PATTERN)
	python3 brepair.py '[**]'  | grep $(PATTERN)
	python3 brepair.py '[**1]'  | grep $(PATTERN)
	python3 brepair.py '[*1*]'  | grep $(PATTERN)
	python3 brepair.py '{ "name": "Dave" "age": 42 }'  | grep $(PATTERN)

# this will fail to repair as expected because the corruption is semantic.
# python3 brepair.py '{"":4,2}'
