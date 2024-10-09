#include <stdint.h>
// #include <string.h>

void *memchr(const void *src, int c, size_t count) {
  const unsigned char *s = src;

  while (count-- != 0) {
    if ((unsigned char)c == *s++) return (void *)(s - 1);
  }

  return NULL;
}

int memcmp(const void *s1, const void *s2, size_t count) {
  const unsigned char *s = s1;
  const unsigned char *d = s2;
  unsigned char sc;
  unsigned char dc;

  while (count--) {
    sc = *s++;
    dc = *d++;
    if (sc - dc) return sc - dc;
  }

  return 0;
}

void *memcpy(void *dst, const void *src, size_t count) {
  const char *s = src;
  char *d = dst;

  while (count--) *d++ = *s++;

  return dst;
}

void *memmove(void *dst, const void *src, size_t count) {
  unsigned char *d = dst;
  const unsigned char *s = src;
  if (dst == src) return dst;

  if (dst < src) return memcpy(dst, src, count);

  while (count--) d[count] = s[count];

  return dst;
}

void *memset(void *dst, int val, size_t count) {
  uint8_t *ptr = dst;
  uint64_t *ptr64;
  uint64_t fill = (unsigned char)val;

  if (count == 0) return dst;

  while (((uintptr_t)ptr & 7) != 0) {
    *ptr = (uint8_t)val;
    ptr++;
    if (--count == 0) return dst;
  }

  fill |= fill << 8;
  fill |= fill << 16;
  fill |= fill << 32;

  ptr64 = (uint64_t *)ptr;
  for (; count >= 8; count -= 8) {
    *ptr64 = fill;
    ptr64++;
  }

  ptr = (uint8_t *)ptr64;
  while (count-- > 0) {
    *ptr = (uint8_t)val;
    ptr++;
  }

  return dst;
}

char *strchr(const char *p, int ch) {
  for (; *p != (char)ch; ++p)
    if (*p == '\0') return NULL;
  return (char *)p;
}

char *strrchr(const char *s, int i) {
  const char *last = NULL;
  char c = i;

  if (c) {
    while ((s = strchr(s, c))) {
      last = s;
      s++;
    }
  } else {
    last = strchr(s, c);
  }

  return (char *)last;
}

char *strcat(char *dest, const char *src) {
  char *tmp = dest;

  while (*dest) dest++;
  while ((*dest++ = *src++) != '\0')
    ;

  return tmp;
}


int strcmp(const char *s1, const char *s2) {
  unsigned char c1, c2;

  while (1) {
    c1 = *s1++;
    c2 = *s2++;
    if (c1 != c2) return c1 < c2 ? -1 : 1;
    if (!c1) break;
  }

  return 0;
}

char *strcpy(char *dest, const char *src) {
  char *tmp = dest;

  while ((*dest++ = *src++) != '\0')
    ;

  return tmp;
}

size_t strlen(const char *s) {
  const char *sc;

  for (sc = s; *sc != '\0'; ++sc)
    ;
  return sc - s;
}

size_t strnlen(const char *str, size_t n) {
  const char *start = str;

  while (n-- > 0 && *str) str++;

  return str - start;
}
