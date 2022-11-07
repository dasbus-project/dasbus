# Copyright (C) 2019  Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA
#
PKGNAME = dasbus
VERSION = $(shell awk '/Version:/ { print $$2 }' python-$(PKGNAME).spec)
TAG = v$(VERSION)
PYTHON ?= python3
COVERAGE ?= coverage3

# Container-related
CI_NAME = $(PKGNAME)-ci
CI_IMAGE ?= fedora
CI_TAG ?= latest
CI_CMD ?= make ci

# Arguments used for setup.py call for creating archive
BUILD_ARGS ?= sdist bdist_wheel

# Arguments used by pylint for checking the code.
CHECK_ARGS ?=

.PHONY: clean
clean:
	git clean -idx

.PHONY: container-ci
container-ci:
	podman build \
		--file ".travis/Dockerfile.$(CI_IMAGE)" \
		--build-arg TAG=$(CI_TAG) \
		--tag $(CI_NAME) \
		--pull-always

	podman run \
		--volume .:/dasbus:Z \
		--workdir /dasbus \
		$(CI_NAME) $(CI_CMD)

.PHONY: ci
ci:
	@echo "*** Running CI with $(PYTHON) ***"
	$(PYTHON) --version
	$(MAKE) check
	$(MAKE) test
	$(MAKE) docs

.PHONY: check
check:
	@echo "*** Running pylint ***"
	$(PYTHON) -m pylint --version
	$(PYTHON) -m pylint $(CHECK_ARGS) src/ tests/

.PHONY: test
test:
	@echo "*** Running unittests with $(COVERAGE) ***"
	PYTHONPATH=src $(COVERAGE) run --rcfile=.coveragerc -m unittest discover -v
	$(COVERAGE) combine
	$(COVERAGE) report -m --include="src/*" | tee coverage-report.log

.PHONY: docs
docs:
	$(MAKE) -C docs html text

.PHONY: changelog
changelog:
	@git log --no-merges --pretty="format:- %s (%ae)" $(TAG).. | sed -e 's/@.*)/)/'

.PHONY: commit
commit:
	@NEWSUBVER=$$((`echo $(VERSION) | cut -d . -f 2` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER | cut -d . -f 1,3` ; \
	DATELINE="* `LC_ALL=C.UTF-8 date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog python-${PKGNAME}.spec | cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) python-${PKGNAME}.spec > speclog ; \
	(head -n $$cl python-${PKGNAME}.spec ; echo "$$DATELINE" ; make --quiet changelog 2>/dev/null ; echo ""; cat speclog) > python-${PKGNAME}.spec.new ; \
	mv python-${PKGNAME}.spec.new python-${PKGNAME}.spec ; rm -f speclog ; \
	sed -i "s/Version:\( *\)$(VERSION)/Version:\1$$NEWVERSION/" python-${PKGNAME}.spec ; \
	sed -i "s/version=\"$(VERSION)\"/version=\"$$NEWVERSION\"/" setup.py ; \
	git add python-${PKGNAME}.spec setup.py ; \
	git commit -m "New release: $$NEWVERSION"

.PHONY: tag
tag:
	git tag -a -m "Tag as $(VERSION)" -f $(TAG)
	@echo "Tagged as $(TAG)"

.PHONY: push
push:
	@echo "Run the command 'git push --follow-tags' with '--dry-run' first."

.PHONY: archive
archive:
	$(PYTHON) setup.py ${BUILD_ARGS}
	@echo "The archive is in dist/$(PKGNAME)-$(VERSION).tar.gz"

.PHONY: upload
upload:
	$(PYTHON) -m twine upload dist/*
