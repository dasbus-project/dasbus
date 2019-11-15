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
PKGNAME=dasbus
VERSION=$(shell awk '/Version:/ { print $$2 }' python-$(PKGNAME).spec)

PREFIX=/usr

PYTHON?=python3
COVERAGE?=coverage3

build:
	$(PYTHON) setup.py build

clean:
	$(PYTHON) setup.py -q clean --all

coverage:
	@echo "*** Running unittests with $(COVERAGE) ***"
	PYTHONPATH=. $(COVERAGE) run --branch -m unittest discover -v -s tests/
	$(COVERAGE) report -m --include="dasbus/*" | tee coverage-report.log

install:
	$(PYTHON) setup.py install --root=$(DESTDIR) --skip-build

tag:
	git tag -a -m "Tag as $(VERSION)" -f v$(VERSION)
	@echo "Tagged as $(VERSION)"

archive: check tag
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ $(VERSION) > $(PKGNAME)-$(VERSION).tar
	gzip -9 $(PKGNAME)-$(VERSION).tar
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

release-pypi:
	if ! $(PYTHON) setup.py sdist bdist_wheel; then \
		echo ""; \
		echo Distribution package build failed! Please verify that you have \'python3-wheel\' and \'python3-setuptools\' installed. >&2; \
		exit 1; \
	fi
	if ! $(PYTHON) -m twine upload dist/*; then \
		echo ""; \
		echo Package upload failed! Make sure the \'twine tool\' is installed and you are registered >&2; \
		exit 1; \
	fi

local:
	@rm -rf $(PKGNAME)-$(VERSION).tar.gz
	@rm -rf /tmp/$(PKGNAME)-$(VERSION) /tmp/$(PKGNAME)
	@dir=$$PWD; cp -a $$dir /tmp/$(PKGNAME)-$(VERSION)
	@cd /tmp/$(PKGNAME)-$(VERSION) ; $(PYTHON) setup.py -q sdist
	@cp /tmp/$(PKGNAME)-$(VERSION)/dist/$(PKGNAME)-$(VERSION).tar.gz .
	@rm -rf /tmp/$(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(VERSION).. |sed -e 's/@.*)/)/' | grep -v "Merge pull request"

bumpver:
	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 2` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,3` ; \
	DATELINE="* `LC_ALL=C.UTF-8 date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog python-${PKGNAME}.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) python-${PKGNAME}.spec > speclog ; \
	(head -n $$cl python-${PKGNAME}.spec ; echo "$$DATELINE" ; make --quiet rpmlog 2>/dev/null ; echo ""; cat speclog) > python-${PKGNAME}.spec.new ; \
	mv python-${PKGNAME}.spec.new python-${PKGNAME}.spec ; rm -f speclog ; \
	sed -i "s/Version:   $(VERSION)/Version:   $$NEWVERSION/" python-${PKGNAME}.spec ; \
	sed -i "s/version='$(VERSION)'/version='$$NEWVERSION'/" setup.py

.PHONY: clean install tag archive local
