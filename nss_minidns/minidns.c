#include <nss.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>

#define SERVER_ADDR     "127.0.0.1"     /* localhost */
#define MINIDNS_PORT    5054
#define MAXBUF          1024

/* http://www.gnu.org/software/libc/manual/html_node/NSS-Modules-Interface.html */

void lamelog(const char *message) {
    FILE *f;
    f = fopen("/tmp/minidns.log", "a");
    fprintf(f, "%s\n", message);
    fclose(f);
}

enum nss_status _nss_minidns_gethostbyname3_r (const char *name, int af, struct hostent *result, char *buffer, size_t buflen, int *errnop, int *h_errnop, int32_t *ttlp, char **canonp) {
    return NSS_STATUS_NOTFOUND;
}


enum nss_status _nss_minidns_gethostbyname2_r (const char *name, int af, struct hostent *result, char *buffer, size_t buflen, int *errnop, int *h_errnop) {
    int sockfd;
    struct sockaddr_in dest;
    char response[MAXBUF];

    lamelog("Starting Query");
    /*---Open socket for streaming---*/
    if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 ) {
        // perror("Socket");
        lamelog("Socket error");
        return NSS_STATUS_NOTFOUND;
    }

    /*---Initialize server address/port struct---*/
    bzero(&dest, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_port = htons(MINIDNS_PORT);
    if ( inet_aton(SERVER_ADDR, &dest.sin_addr.s_addr) == 0 ) {
        // perror(SERVER_ADDR);
        lamelog("Address error");
        return NSS_STATUS_NOTFOUND;
    }

    /*---Connect to server---*/
    if ( connect(sockfd, (struct sockaddr*)&dest, sizeof(dest)) != 0 ) {
        // perror("Connect ");
        lamelog("Connect error");
        return NSS_STATUS_NOTFOUND;
    }

    send(sockfd, name, strlen(name), 0);
    bzero(response, MAXBUF);
    recv(sockfd, response, sizeof(response), 0);
    lamelog(response);

    /*---Clean up---*/
    close(sockfd);
    return NSS_STATUS_NOTFOUND;
}

enum nss_status _nss_minidns_gethostbyname_r (const char *name, struct hostent *result, char *buffer, size_t buflen, int *errnop, int *h_errnop) {
    return NSS_STATUS_NOTFOUND;
}

enum nss_status _nss_minidns_gethostbyname4_r (const char *name, struct gaih_addrtuple **pat, char *buffer, size_t buflen, int *errnop, int *herrnop, int32_t *ttlp) {
    return NSS_STATUS_NOTFOUND;
}
