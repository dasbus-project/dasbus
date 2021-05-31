%global srcname dasbus

Name:           python-%{srcname}
Version:        1.6
Release:        1%{?dist}
Summary:        DBus library in Python 3

License:        LGPLv2+
URL:            https://pypi.python.org/pypi/dasbus
%if %{defined suse_version}
Source0:        %{srcname}-%{version}.tar.gz
%else
Source0:        %{pypi_source}
%endif

BuildArch:      noarch

%global _description %{expand:
Dasbus is a DBus library written in Python 3, based on
GLib and inspired by pydbus. It is designed to be easy
to use and extend.}

%description %{_description}

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
%if %{defined suse_version}
Requires:       python3-gobject
%else
Requires:       python3-gobject-base
%endif
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname} %{_description}

%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/%{srcname}-*.egg-info/
%{python3_sitelib}/%{srcname}/

%changelog
* Mon May 31 2021 Vendula Poncova <vponcova@redhat.com> - 1.6-1
- Add support for SUSE packaging in spec file (christopher.m.cantalupo)
- Allow to generate multiple output arguments (vponcova)
- Support multiple output arguments (vponcova)
- Add the is_tuple_of_one function (vponcova)
- Configure the codecov tool (vponcova)
* Mon May 03 2021 Vendula Poncova <vponcova@redhat.com> - 1.5-1
- Disable builds for Fedora ELN on pull requests (vponcova)
- Provide additional info about the DBus call (vponcova)
- Run the codecov uploader from a package (vponcova)
- Switch to packit new fedora-latest alias (jkonecny)
- Add daily builds for our Fedora-devel COPR repository (jkonecny)
- Use Fedora container registry instead of Dockerhub (jkonecny)
- Migrate daily COPR builds to Packit (jkonecny)
- Switch Packit tests to copr builds instead (jkonecny)
- Enable Packit build in ELN chroot (jkonecny)
- Rename TestMessageBus class to silence pytest warning (luca)
- Fix the raise-missing-from warning (vponcova)
* Fri Jul 24 2020 Vendula Poncova <vponcova@redhat.com> - 1.4-1
- Handle all errors of the DBus call (vponcova)
- Fix tests for handling DBus errors on the server side (vponcova)
- Run packit smoke tests for all Fedora (jkonecny)
- Fix packit archive creation (jkonecny)
- Add possibility to change setup.py arguments (jkonecny)
* Wed Jun 17 2020 Vendula Poncova <vponcova@redhat.com> - 1.3-1
- Document differences between dasbus and pydbus (vponcova)
- Improve the support for interface proxies in the service identifier (vponcova)
- Improve the support for interface proxies in the message bus (vponcova)
- Test the interface proxies (vponcova)
- Make the message bus of a service identifier accessible (vponcova)
- Fix the testing environment for Fedora Rawhide (vponcova)
* Mon May 18 2020 Vendula Poncova <vponcova@redhat.com> - 1.2-1
- Replace ABC with ABCMeta (vponcova)
- Fix typing tests (vponcova)
- Run tests on the latest CentOS (vponcova)
- Install sphinx from PyPI (vponcova)
* Thu May 14 2020 Vendula Poncova <vponcova@redhat.com> - 1.1-1
- Include tests and examples in the source distribution (vponcova)
- Fix the pylint warning signature-differs (vponcova)
* Tue May 05 2020 Vendula Poncova <vponcova@redhat.com> - 1.0-1
- Fix the documentation (vponcova)
- Fix minor typos (yurchor)
- Enable Codecov (vponcova)
- Test the documentation build (vponcova)
- Extend the documentation (vponcova)
- Add configuration files for Read the Docs and Conda (vponcova)
- Fix all warnings from the generated documentation (vponcova)
* Wed Apr 08 2020 Vendula Poncova <vponcova@redhat.com> - 0.4-1
- Replace the error register with the error mapper (vponcova)
- Propagate additional arguments for the client handler factory (vponcova)
- Propagate additional arguments in the class AddressedMessageBus (vponcova)
- Generate the documentation (vponcova)
* Thu Apr 02 2020 Vendula Poncova <vponcova@redhat.com> - 0.3-1
- Remove generate_dictionary_from_data (vponcova)
- Improve some of the error messages (vponcova)
- Check the list of DBus structures to convert (vponcova)
- Add the Inspiration section to README (vponcova)
- Enable syntax highlighting in README (vponcova)
- Use the class EventLoop in README (vponcova)
- Use the --no-merges option (vponcova)
- Clean up the Makefile (vponcova)
- Add examples (vponcova)
- Add the representation of the event loop (vponcova)
- Enable copr builds and add packit config (dhodovsk)
- Extend README (vponcova)
* Mon Jan 13 2020 Vendula Poncova <vponcova@redhat.com> - 0.2-1
- Unwrap DBus values (vponcova)
- Unwrap a variant data type (vponcova)
- Add a default DBus error (vponcova)
- Use the minimal image in Travis CI (vponcova)
- Remove GLibErrorHandler (vponcova)
- Remove map_error and map_by_default (vponcova)
- Extend arguments of dbus_error (vponcova)
- Extend arguments of dbus_interface (vponcova)
- The list of callbacks in signals can be changed during emitting (vponcova)
- Don't import from mock (vponcova)
- Enable checks in Travis CI (vponcova)
- Fix too long lines (vponcova)
- Don't use wildcard imports (vponcova)
- Add the check target to the Makefile (vponcova)
- Enable Travis CI (vponcova)
- Catch logged warnings in the unit tests (vponcova)
- Add the coverage target to the Makefile (vponcova)
- Rename tests (vponcova)
- Create Makefile (vponcova)
- Create a .spec file (vponcova)
- Add requirements to the README file (vponcova)

* Thu Oct 31 2019 Vendula Poncova <vponcova@redhat.com> - 0.1-1
- Initial package
