// author : zuoqian
// Copyright 2023. All rights reserved.

#include "dw16550.h"

enum {
  RXFE = 0x10,
  TXFE = 0x20,
};

typedef volatile struct {
  union {
    const uint32_t RBR;
    uint32_t THR;  // WO
    uint32_t DLL;  // LCR[7] = 1
  };
  union {
    uint32_t DLH;  // LCR[7] = 1
    uint32_t IER;
  };
  union {
    const uint32_t IIR;
    uint32_t FCR;  // WO
  };
  uint32_t LCR;
  uint32_t MCR;
  const uint32_t LSR;
  const uint32_t MSR;
  uint32_t SCR;
  uint32_t LPDLL;
  uint32_t LPDLH;
  const uint32_t reserved0[2];
  union {
    const uint32_t SRBR[16];
    uint32_t STHR[16];  // WO
  };
  uint32_t FAR;
  const uint32_t TFR;
  uint32_t RFW;  // WO
  const uint32_t USR;
  const uint32_t TFL;
  const uint32_t RFL;
  uint32_t SRR;  // WO
  uint32_t SRTS;
  uint32_t SBCR;
  uint32_t SDMAM;
  uint32_t SFE;
  uint32_t SRT;
  uint32_t STET;
  uint32_t HTX;
  uint32_t DMASA;  // WO
  const uint32_t reserved1[18];
  const uint32_t CPR;
  const uint32_t UCV;
  const uint32_t CTR;
} dw16550_t;

/* FIFO Control Register bits */
#define UARTFCR_FIFOMD_16450 (0 << 6)
#define UARTFCR_FIFOMD_16550 (1 << 6)
#define UARTFCR_RXTRIG_1 (0 << 6)
#define UARTFCR_RXTRIG_4 (1 << 6)
#define UARTFCR_RXTRIG_8 (2 << 6)
#define UARTFCR_RXTRIG_16 (3 << 6)
#define UARTFCR_TXTRIG_1 (0 << 4)
#define UARTFCR_TXTRIG_4 (1 << 4)
#define UARTFCR_TXTRIG_8 (2 << 4)
#define UARTFCR_TXTRIG_16 (3 << 4)
#define UARTFCR_DMAEN (1 << 3)  /* Enable DMA mode */
#define UARTFCR_TXCLR (1 << 2)  /* Clear contents of Tx FIFO */
#define UARTFCR_RXCLR (1 << 1)  /* Clear contents of Rx FIFO */
#define UARTFCR_FIFOEN (1 << 0) /* Enable the Tx/Rx FIFO */

/* Line Control Register bits */
#define UARTLCR_DLAB (1 << 7) /* Divisor Latch Access */
#define UARTLCR_SETB (1 << 6) /* Set BREAK Condition */
#define UARTLCR_SETP (1 << 5) /* Set Parity to LCR[4] */
#define UARTLCR_EVEN (1 << 4) /* Even Parity Format */
#define UARTLCR_PAR (1 << 3)  /* Parity */
#define UARTLCR_STOP (1 << 2) /* Stop Bit */
#define UARTLCR_WORDSZ_5 0    /* Word Length of 5 */
#define UARTLCR_WORDSZ_6 1    /* Word Length of 6 */
#define UARTLCR_WORDSZ_7 2    /* Word Length of 7 */
#define UARTLCR_WORDSZ_8 3    /* Word Length of 8 */

/* Line Status Register bits */
#define UARTLSR_RXFIFOERR (1 << 7) /* Rx Fifo Error */
#define UARTLSR_TEMT (1 << 6)      /* Tx Shift Register Empty */
#define UARTLSR_THRE (1 << 5)      /* Tx Holding Register Empty */
#define UARTLSR_BRK (1 << 4)       /* Break Condition Detected */
#define UARTLSR_FERR (1 << 3)      /* Framing Error */
#define UARTLSR_PERR (1 << 2)      /* Parity Error */
#define UARTLSR_OVRF (1 << 1)      /* Rx Overrun Error */
#define UARTLSR_RDR (1 << 0)       /* Rx Data Ready */

#define DW16550_CLOCK 50000000

static int initialized = 0;

void dw16550_init(uint64_t base, unsigned int baudrate) {
  dw16550_t* uart = (dw16550_t*)base;
  uint16_t brd = (DW16550_CLOCK / (16 * baudrate));

  uart->LCR |= UARTLCR_DLAB;
  uart->DLL = (brd & 0xff);
  uart->DLH = ((brd >> 8) & 0xff);
  uart->LCR &= ~UARTLCR_DLAB;

  uart->LCR = UARTLCR_WORDSZ_8;  // 8N1
  uart->IER = 0;
  uart->FCR = UARTFCR_TXCLR | UARTFCR_RXCLR | UARTFCR_FIFOEN;  // also reset
                                                               // FIFO
  // uart->FCR = UARTFCR_FIFOEN;

  initialized = 1;
}

void dw16550_putchar(uint64_t base, char c) {
  dw16550_t* uart = (dw16550_t*)base;
  if (c == '\n') {
    while (!(uart->LSR & UARTLSR_THRE))
      ;
    uart->THR = '\r';
  }
  while (!(uart->LSR & UARTLSR_THRE))
    ;
  uart->THR = c;
}

// int dw16550_getchar(dw16550_t* uart) {
//   if (initialized) {
//     while (!(uart->LSR & UARTLSR_RDR))
//       ;
//   }
//   return uart->RBR;
// }
