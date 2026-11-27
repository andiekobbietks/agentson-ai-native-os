#ifndef AGENTSON_SERIAL_H
#define AGENTSON_SERIAL_H

#include <stdint.h>

void serial_init(void);
void serial_write(const char *value);
void serial_write_hex32(uint32_t value);
void serial_write_hex64(uint64_t value);

#endif
