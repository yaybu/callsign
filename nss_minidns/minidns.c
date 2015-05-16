#include <nss.h>
#include <pwd.h>
#include <grp.h>

enum nss_status _nss_minidns_setpwent (void);
enum nss_status _nss_minidns_endpwent (void);
enum nss_status _nss_minidns_getpwent_r (struct passwd *result, char *buffer, size_t buflen, int *errnop);
enum nss_status _nss_minidns_getpwbyuid_r (uid_t uid, struct passwd *result, char *buffer, size_t buflen, int *errnop);
enum nss_status _nss_minidns_getpwbynam_r (const char *name, struct passwd *result, char *buffer, size_t buflen, int *errnop);

