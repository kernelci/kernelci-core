#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>

static const char DEFAULT_OS_NAME[] = "Linux";

int main(int argc, char **argv)
{
	const char *os_name = DEFAULT_OS_NAME;
	struct utsname uts;
	int res;

	if (argc > 1)
		os_name = argv[1];

	uname(&uts);
	res = strcmp(uts.sysname, os_name);
	res = res ? EXIT_FAILURE : EXIT_SUCCESS;

	printf("System: '%s', expected: '%s', result: %s\n",
	       uts.sysname, os_name, res ? "FAIL" : "PASS");

	return res;
}
