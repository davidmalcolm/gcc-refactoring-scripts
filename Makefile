all:
	python test_refactor.py -v
	python test_refactor_cfun.py -v
	python test_refactor_options.py -v
	python test_refactor_passes.py -v
	python test_refactor_symtab.py -v
