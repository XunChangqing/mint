// author : zuoqian
// Copyright 2023. All rights reserved.

#include "dw16550.h"

enum {
  RXFE = 0x10,
  TXFE = 0x20,
};

typedef volatile struct {
  union {
    const u32 RBR;
    u32 THR;  // WO
    u32 DLL;  // LCR[7] = 1
  };
  union {
    u32 DLH;  // LCR[7] = 1
    u32 IER;
  };
  union {
    const u32 IIR;
    u32 FCR;  // WO
  };
  u32 LCR;
  u32 MCR;
  const u32 LSR;
  const u32 MSR;
  u32 SCR;
  u32 LPDLL;
  u32 LPDLH;
  const u32 reserved0[2];
  union {
    const u32 SRBR[16];
    u32 STHR[16];  // WO
  };
  u32 FAR;
  const u32 TFR;
  u32 RFW;  // WO
  const u32 USR;
  const u32 TFL;
  const u32 RFL;
  u32 SRR;  // WO
  u32 SRTS;
  u32 SBCR;
  u32 SDMAM;
  u32 SFE;
  u32 SRT;
  u32 STET;
  u32 HTX;
  u32 DMASA;  // WO
  const u32 reserved1[18];
  const u32 CPR;
  const u32 UCV;
  const u32 CTR;
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

void dw16550_init(unsigned long base, unsigned int baudrate) {
  dw16550_t* uart = (dw16550_t*)base;
  u16 brd = (DW16550_CLOCK / (16 * baudrate));

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

void dw16550_putchar(unsigned long base, char c) {
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
