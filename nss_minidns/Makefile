
libnss_minidns.so.2: minidns.o
	gcc -fPIC -shared -o libnss_minidns.so.2 -Wl,-soname,libnss_minidns.so.2 minidns.o
	
minidns.o: minidns.c
	gcc -c -fPIC -o minidns.o minidns.c

install:
	install -m 0644 libnss_minidns.so.2 /lib
	/sbin/ldconfig -n /lib /usr/lib

