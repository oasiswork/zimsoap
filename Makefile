.PHONY: docs

lint:
	flake8 --exclude=build,dist,tests/samples.py .

docs:
	$(MAKE) -C docs html
	@echo "Open docs/build/html/index.html to view documentation"
