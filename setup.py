#Copyright 2013 Isotoma Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from setuptools import setup, find_packages

version = '0.4.dev0'

setup(
    name="callsign",
    version=version,
    description="Simple DNS Server with REST API, for localhost only",
    url="http://github.com/yaybu/callsign",
    long_description=open("README.rst").read(),
    author="Doug Winter",
    author_email="doug.winter@isotoma.com",
    license="Apache Software License",
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Internet :: Name Service (DNS)",
    ],
    packages=find_packages(),
    install_requires=[
        'Twisted',
        'requests',
    ],
    extras_require={
        'test': ['mock'],
    },
    entry_points={
        "console_scripts": [
            "callsigncmd=callsign.scripts.command:run",
            "callsign-daemon=callsign.scripts.daemon:run",
        ]
    }
)
