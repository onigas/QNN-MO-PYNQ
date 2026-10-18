#ifndef QNN_RPI_DARKNET_COMPAT_H
#define QNN_RPI_DARKNET_COMPAT_H
#include "darknet.h"
/* Missing in the legacy fork's headers; avoid pointer truncation on ARM64. */
image **load_alphabet_path(char *path);
#endif
