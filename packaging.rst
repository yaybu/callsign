How i built this package.

from here https://wiki.debian.org/Python/Packaging

pip install stdeb (in the virtualenv)
python setup.py --command-packages=stdeb.command debianize
cp LICENSE debian/copyright
sudo apt-get install devscripts
debuild

follow the "python application" instructions at python packaging:

edit the control file
edit the rules file
create the links file
rename the script in setup.py
build it with debuild
install it

