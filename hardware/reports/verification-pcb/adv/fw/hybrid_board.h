#pragma once

// ///////////////////////////////////////////////////////////// //
// Hardware abstraction layer for all different supported boards //
// ///////////////////////////////////////////////////////////// //
#include "board/boards/board_declarations.h"
#include "board/boards/unused_funcs.h"

// ///// Board definition and detection ///// //
#include "board/stm32h7/lladc.h"
#include "board/stm32h7/lldts.h"
#include "board/drivers/harness.h"
#include "board/drivers/fan.h"
#include "board/stm32h7/llfan.h"
#include "board/stm32h7/sound.h"
#include "board/drivers/fake_siren.h"
#include "board/drivers/clock_source.h"
#ifndef HYBRID_BOARD
#include "board/boards/red.h"
#include "board/boards/tres.h"
#include "board/boards/cuatro.h"
#endif
#include "board/boards/hybrid.h"


void detect_board_type(void) {
#ifdef HYBRID_BOARD
  // Hybrid Panda build: the board is known at compile time. Boards shipped with
  // PF9 still strapped to GND read id1 == 0 (red) and would otherwise get the red
  // panda PB14 (USB-A load switch) handling, so the straps are ignored here.
  hw_type = HW_TYPE_HYBRID_PANDA;
  current_board = &board_hybrid;
#else
  // On STM32H7 pandas, we use two different sets of pins.
  const uint8_t id1 = detect_with_pull(GPIOF, 7, PULL_UP) |
                     (detect_with_pull(GPIOF, 8, PULL_UP) << 1U) |
                     (detect_with_pull(GPIOF, 9, PULL_UP) << 2U) |
                     (detect_with_pull(GPIOF, 10, PULL_UP) << 3U);

  const uint8_t id2 = detect_with_pull(GPIOD, 4, PULL_UP) |
                     (detect_with_pull(GPIOD, 5, PULL_UP) << 1U) |
                     (detect_with_pull(GPIOD, 6, PULL_UP) << 2U) |
                     (detect_with_pull(GPIOD, 7, PULL_UP) << 3U);

  if (id2 == 3U) {
    hw_type = HW_TYPE_CUATRO;
    current_board = &board_cuatro;
  } else if (id1 == 0U) {
    hw_type = HW_TYPE_RED_PANDA;
    current_board = &board_red;
  } else if (id1 == 1U) {
    // deprecated
    //hw_type = HW_TYPE_RED_PANDA_V2;
    hw_type = HW_TYPE_UNKNOWN;
  } else if (id1 == 2U) {
    hw_type = HW_TYPE_TRES;
    current_board = &board_tres;
  } else if (id1 == 4U) {
    // Hybrid Panda: PF7, PF8, PF10 strapped to GND, PF9 left open (read high by the pull-up).
    // Red is id1 == 0 (all four GND) and tres is id1 == 2 (only PF8 open), so the
    // single PF9 strap cannot alias either of them.
    hw_type = HW_TYPE_HYBRID_PANDA;
    current_board = &board_hybrid;
  } else {
    hw_type = HW_TYPE_UNKNOWN;
    print("Hardware type is UNKNOWN!\n");
  }
#endif
}
