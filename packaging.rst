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

now for the panel applet stuff.

http://www.lshift.net/blog/2012/02/29/making-panel-applets-for-gnome-2-and-3/


