%global srcname dasbus

Name:           python-%{srcname}
Version:        0.1
Release:        1%{?dist}
Summary:        DBus library in Python 3

License:        LGPLv2+
URL:            https://pypi.python.org/pypi/dasbus
Source0:        %{pypi_source}

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
Requires:       python3-gobject-base
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
* Thu Oct 31 2019 Vendula Poncova <vponcova@redhat.com> - 0.1-1
- Initial package
