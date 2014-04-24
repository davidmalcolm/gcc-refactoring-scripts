all:
	python test_refactor.py -v
	python test_refactor_cfun.py -v
	#python test_refactor_gimple.py -v
	python test_refactor_ipa_passes.py -v
	python test_refactor_options.py -v
	python test_refactor_passes.py -v
	python test_refactor_symtab.py -v
	python test_rename_symtab.py -v
	python test_rename_gimple.py -v

html:
	rst2html README.rst > README.html
