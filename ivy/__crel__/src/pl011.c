// author : zuoqian
// Copyright 2023. All rights reserved.

#include "pl011.h"

#define __IO volatile
#define __IM volatile const

typedef struct {
  __IO uint32_t DR;
  __IO uint32_t RSR_ECR;
  __IO uint8_t reserved0[0x10];
  __IM uint32_t FR;
  __IO uint8_t reserved1[0x4];
  __IO uint32_t LPR;
  __IO uint32_t IBRD;
  __IO uint32_t FBRD;
  __IO uint32_t LCR_H;
  __IO uint32_t CR;
  __IO uint32_t IFLS;
  __IO uint32_t IMSC;
  __IM uint32_t RIS;
  __IM uint32_t MIS;
  __IO uint32_t ICR;
  __IO uint32_t DMACR;
} pl011regs;

/// @name CFG - UART UARTLCR_H Register
#define UART_LCR_FEN_SHIFT 4U
#define UART_LCR_FEN_MASK 0x10U

#define UART_LCR_WLEN_SHIFT 5U
#define UART_LCR_WLEN_MASK 0x60U
/// @}

/// @name CFG - UART UARTCR Register
#define UART_CR_UARTEN_SHIFT 0U
#define UART_CR_UARTEN_MASK 0x1U

#define UART_CR_TXE_SHIFT 8U
#define UART_CR_TXE_MASK 0x100U

#define UART_CR_RXE_SHIFT 9U
#define UART_CR_RXE_MASK 0x200U
/// @}

/// @name CFG - UART UARTIBRD Register
#define UART_IBRD_SHIFT 6U
#define UART_IBRD_MASK 0xFFFFU

/// @}

/// @name CFG - UART UARTFBRD Register
#define UART_FBRD_SHIFT 0U
#define UART_FBRD_MASK 0x3FU
/// @}

/// @name CFG - UART UARTFR Register
#define UART_FR_TXFE_MASK 0x80U
#define UART_FR_RXFF_MASK 0x40U
#define UART_FR_TXFF_MASK 0x20U
#define UART_FR_RXFE_MASK 0x10U
#define UART_FR_BUSY_MASK 0x08U
/// @}

/** UART的时钟 */
#define UART_CLOCK 50000000
// #define UART_CLOCK 24000000

#define UART_CFG_IBRD(x) \
  (((uint32_t)(((uint32_t)(x)) >> UART_IBRD_SHIFT)) & UART_IBRD_MASK)
#define UART_GET_IBRD(x) \
  (((uint32_t)(((uint32_t)(x)) & UART_IBRD_MASK)) << UART_IBRD_SHIFT)

/** @brief  设置32位寄存器得值*/
#define SET_REG32(x, dev, reg) \
  (((uint32_t)(((uint32_t)(x)) << dev##_##reg##_SHIFT)) & dev##_##reg##_MASK)

/** @brief  获得32位寄存器的值*/
#define GET_REG32(x, dev, reg) \
  (((uint32_t)(((uint32_t)(x)) & dev##_##reg##_MASK)) >> dev##_##reg##_SHIFT)

/** @brief 设置64位寄存器得值*/
#define SET_REG64(x, dev, reg) \
  (((uint64_t)(((uint64_t)(x)) << dev##_##reg##_SHIFT)) & dev##_##reg##_MASK)

/** @brief  获得64位寄存器的值*/
#define GET_REG64(x, dev, reg) \
  (((uint64_t)(((uint64_t)(x)) & dev##_##reg##_MASK)) >> dev##_##reg##_SHIFT)

// void UART_GetDefaultCfg(uart *cfg) {
//   uart_t tmpConfig;

//   tmpConfig.baudrate = 115200;
//   tmpConfig.bitcount = eUart_8BitsPerchar;
//   tmpConfig.enablefifo = true;
//   tmpConfig.enablerx = true;
//   tmpConfig.enabletx = true;
//   tmpConfig.enableuart = true;

//   (*cfg) = tmpConfig;
// }

void pl011_init(uint64_t base_addr, pl011_cfg *cfg) {
  uint32_t p = 0;
  uint64_t brd = ((UART_CLOCK << 2) / cfg->baudrate);
  pl011regs *base = (pl011regs *)base_addr;
  base->IBRD = UART_CFG_IBRD(brd);
  // base->IBRD = SET_REG32(brd, UART, IBRD);
  base->FBRD = SET_REG32(brd, UART, FBRD);

  p |= SET_REG32(cfg->enablefifo, UART, LCR_FEN);
  p |= SET_REG32(cfg->bitcount, UART, LCR_WLEN);
  base->LCR_H = p;

  p = 0;
  base->RSR_ECR = 0;
  p |= SET_REG32(cfg->enableuart, UART, CR_UARTEN);
  p |= SET_REG32(cfg->enabletx, UART, CR_TXE);
  p |= SET_REG32(cfg->enablerx, UART, CR_RXE);
  base->CR = p;
}

void pl011_putchar(uint64_t base_addr, char c) {
  pl011regs *base = (pl011regs *)base_addr;
  if (c == '\n') {
    while (base->FR & UART_FR_TXFF_MASK)
      ;
    base->DR = '\r';
  }
  while (base->FR & UART_FR_TXFF_MASK)
    ;
  base->DR = c;
}
