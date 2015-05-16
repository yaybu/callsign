#include <stdio.h>
#include <nss.h>
#include <netdb.h>

/* http://www.gnu.org/software/libc/manual/html_node/NSS-Modules-Interface.html */

void lamelog(const char *message) {
    FILE *f;
    f = fopen("/tmp/minidns.log", "a");
    fprintf(f, "%s\n", message);
    fclose(f);
}

enum nss_status _nss_minidns_gethostbyname3_r (const char *name, int af, struct hostent *result, char *buffer, size_t buflen, int *errnop, int *h_errnop, int32_t *ttlp, char **canonp) {
    lamelog("gethostbyname3");
    lamelog(name);
}


enum nss_status _nss_minidns_gethostbyname2_r (const char *name, int af, struct hostent *result, char *buffer, size_t buflen, int *errnop, int *h_errnop) {
    lamelog("gethostbyname2");
    lamelog(name);
}

enum nss_status _nss_minidns_gethostbyname_r (const char *name, struct hostent *result, char *buffer, size_t buflen, int *errnop, int *h_errnop) {
    lamelog("gethostbyname");
    lamelog(name);
}

enum nss_status _nss_minidns_gethostbyname4_r (const char *name, struct gaih_addrtuple **pat, char *buffer, size_t buflen, int *errnop, int *herrnop, int32_t *ttlp) {
    lamelog("gethostbyname4");
    lamelog(name);

}
