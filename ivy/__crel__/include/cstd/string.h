#pragma once
#include "stdint.h"

// static void *malloc(size_t len);

int memcmp(const void *s1, const void *s2, size_t n);
void *memmove(void *dst, const void *src, size_t len);
void *memcpy(void *dst, const void *src, size_t len);
void *memset(void *dst, int b, size_t len);
char *strchr(const char *s, int c);
int strcmp(const char *a, const char *b);
char *strcpy(char *dst, const char *src);
size_t strlen(const char *str);
size_t strnlen(const char *str, size_t maxlen);

// static __attribute__((unused))
// char *strdup(const char *str)
// {
// 	size_t len;
// 	char *ret;

// 	len = strlen(str);
// 	ret = malloc(len + 1);
// 	if (__builtin_expect(ret != NULL, 1))
// 		memcpy(ret, str, len + 1);

// 	return ret;
// }

// static __attribute__((unused))
// char *strndup(const char *str, size_t maxlen)
// {
// 	size_t len;
// 	char *ret;

// 	len = strnlen(str, maxlen);
// 	ret = malloc(len + 1);
// 	if (__builtin_expect(ret != NULL, 1)) {
// 		memcpy(ret, str, len);
// 		ret[len] = '\0';
// 	}

// 	return ret;
// }

static __attribute__((unused))
size_t strlcat(char *dst, const char *src, size_t size)
{
	size_t len;
	char c;

	for (len = 0; dst[len];	len++)
		;

	for (;;) {
		c = *src;
		if (len < size)
			dst[len] = c;
		if (!c)
			break;
		len++;
		src++;
	}

	return len;
}

static __attribute__((unused))
size_t strlcpy(char *dst, const char *src, size_t size)
{
	size_t len;
	char c;

	for (len = 0;;) {
		c = src[len];
		if (len < size)
			dst[len] = c;
		if (!c)
			break;
		len++;
	}
	return len;
}

static __attribute__((unused))
char *strncat(char *dst, const char *src, size_t size)
{
	char *orig = dst;

	while (*dst)
		dst++;

	while (size && (*dst = *src)) {
		src++;
		dst++;
		size--;
	}

	*dst = 0;
	return orig;
}

int strncmp(const char *a, const char *b, size_t size);

static __attribute__((unused))
char *strncpy(char *dst, const char *src, size_t size)
{
	size_t len;

	for (len = 0; len < size; len++)
		if ((dst[len] = *src))
			src++;
	return dst;
}

char *strrchr(const char *s, int c);
