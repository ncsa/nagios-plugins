# Author: Jon Schipp <jonschipp@gmail.com, jschipp@illinois.edu>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <iso646.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>

#define VERSION_STRING "0.1"

#define OK       0
#define WARNING  1
#define CRITICAL 2
#define UNKNOWN  3

static void usage(void)
{
    printf("check_nfs_stale Version: %s\n", VERSION_STRING);
    puts(
    "Nagios plugin to check for stale NFS mounts\n"
    "Options:\n\n"
    " -p <mount> Mount point of NFS share\n"
    " -h         Print help\n\n"
    "Usage: check_nfs_stale [-h] [-p mount_point]\n"
    "Please report bugs to <jonschipp@gmail.com>");
    exit(OK);
}

int main(int argc, char **argv) {

struct stat file_stat;
int ret, c;
const char *mpoint = NULL;

if ( argc == 1 ) {
    puts("Requires an argument, try ``-h''");
    exit(UNKNOWN);
}

while ((c = getopt (argc, argv, "hp:")) != -1)
switch (c) {
    case 'h':
        usage();
        break;
    case 'p':
        mpoint = optarg;
        break;
    case '?':
        usage();
        break;
}

ret = stat(mpoint, &file_stat);

if (ret == -1 && errno == ESTALE) {
    printf("%s is stale\n", mpoint);
    exit(CRITICAL);
    }
else
    printf("%s is fine\n", mpoint);
    exit(OK);
}
