#pragma once

#include "board_declarations.h"

// ////////////////////////////////////////////////////////////////////////////// //
// Hybrid Panda: black panda hardware + STM32H725ZGT6 (LQFP144) + 4x TJA1042TK/3 //
// ////////////////////////////////////////////////////////////////////////////// //
//
// Open-hardware board (HybridPanda.kicad_sch). Every pin below was taken from
// the schematic netlist (U7 = STM32H725ZGT6), not from the red panda.
//
// | function                  | H725 pin (LQFP144) | net          | note                                        |
// |---------------------------|--------------------|--------------|---------------------------------------------|
// | FDCAN1 RX / TX (bus 0)    | PB8 (136) / PB9 (137)   | BUS0_RX / BUS0_TX   | U11 TJA1042, AF9, harness pins B10/B11  |
// | FDCAN2 RX / TX (bus 1 N)  | PB5 (132) / PB6 (133)   | BUS1N_RX / BUS1N_TX | U10 TJA1042, AF9, harness pins B3/B2    |
// | FDCAN2 RX / TX (bus 1 O)  | PB12 (72) / PB13 (73)   | BUS1O_RX / BUS1O_TX | U8 TJA1042, AF9, harness pins A3/A2     |
// | FDCAN3 RX / TX (bus 2)    | PG10 (123) / PG9 (122)  | BUS2_RX / BUS2_TX   | U9 TJA1042, AF2, harness pins A10/A11   |
// | transceiver 1 STB (bus 0) | PG11 (124)         | BUS0_STB     | 10k pull-up R30, STB high = standby         |
// | transceiver 2 STB (bus 1N)| PB3 (130)          | BUS1N_STB    | 10k pull-up R31                             |
// | transceiver 3 STB (bus 2) | PD7 (121)          | BUS2_STB     | 10k pull-up R33                             |
// | transceiver 4 STB (bus 1O)| PB4 (131)          | BUS1O_STB    | 10k pull-up R32                             |
// | SBU1 sense (ADC1_INP4)    | PC4 (47)           | SBU1_ADC     | 10k R28 + BAT54S D13 clamp, SBU1 10k to 3V3 |
// | SBU2 sense (ADC1_INP17)   | PA1 (38)           | SBU2_ADC     | 10k R29 + BAT54S D14 clamp, SBU2 10k to 3V3 |
// | relay SBU1                | PC10 (109)         | relay_SBU1   | Q2 DDTA143E (PNP, E=+5V, C=SBU1)            |
// | relay SBU2                | PC11 (110)         | relay_SBU2   | Q1 DDTA143E (PNP, E=+5V, C=SBU2)            |
// | 12V sense (ADC1_INP2)     | PF11 (52)          | VoltageSens  | 10k/1k divider (x11) from 12V_Protected     |
// | 5V out sense (ADC1_INP5)  | PB1 (50)           | 5VOUT_S      | 10k/10k divider from +5V                    |
// | USB-A load switch         | PB14 (74)          | USB_LOAD     | Q3 PDTC114EU (NPN, E=GND) -> U1 AP22615 EN (R26 10k to +5V); push-pull, 0 = port ON |
// | LED red / green / blue    | PE4 (3) / PE3 (2) / PE2 (1) | LED_RED/GREEN/BLUE | U5 common anode to 3V3, active low |
// | USB OTG_FS DM / DP        | PA11 (100) / PA12 (101) | USB_D- / USB_D+ | 22R series, USB-A U3 to comma device  |
// | HSE                       | PH0 (25) / PH1 (26)| HSE_IN/OUT   | Y1 25 MHz                                   |
// | SWDIO / SWCLK             | PA13 (102) / PA14 (107) | SWDIO / SWCLK | J1 2x5 1.27mm                          |
// | BOOT0                     | BOOT0 (135)        | BOOT0        | 10k pull-down R14, SW1 to 3V3               |
// | HW type straps id1        | PF7..PF10 (21..24) | GND          | PF7/PF8/PF10 GND, PF9 open = id1 4 (hybrid) |
// | HW type straps id2        | PD4..PD6 (116,117,120) | n.c.     | read 1 with pull-up, PD7 is BUS2_STB        |
// | fan / siren / SOM / SPI   | -                  | -            | absent on this board                        |
//
// Power scheme (from the netlist): VDDLDO (70/105/143) = +3V3, VDDSMPS (16) = +3V3,
// VLXSMPS (15) -> L5 2.2uH -> VFBSMPS (17) with C42 10uF, VCAP (68/103/140) with
// C39/C40 2.2uF. The firmware configures direct SMPS supply on LQFP144
// (see stm32h7/clock.h), which requires VFBSMPS to be connected to VCAP.
//
// Electrically this board is pin-identical to the red panda for every function
// used by the firmware (same CAN pins/AFs, STB polarity, ADC channels, LEDs). The
// only deviation is PB14: red leaves it open-drain high with the internal pull-up,
// which on this board biases Q3 (PDTC114EU, 10k internal base resistor) right
// at its threshold and can pull the AP22615 EN low, switching the USB-A port
// (the comma device's power) off. Here it is driven push-pull: 0 = Q3 off =
// EN pulled to +5V by R26 = port ON, 1 = port OFF. Like the black panda
// (black_set_usb_load_switch(true) at init, never touched again), the port is
// kept on at all times, including power-save mode, because the comma device is
// powered from it.

static void hybrid_enable_can_transceiver(uint8_t transceiver, bool enabled) {
  switch (transceiver) {
    case 1U:
      set_gpio_output(GPIOG, 11, !enabled);
      break;
    case 2U:
      set_gpio_output(GPIOB, 3, !enabled);
      break;
    case 3U:
      set_gpio_output(GPIOD, 7, !enabled);
      break;
    case 4U:
      set_gpio_output(GPIOB, 4, !enabled);
      break;
    default:
      break;
  }
}

static void hybrid_set_can_mode(uint8_t mode) {
  hybrid_enable_can_transceiver(2U, false);
  hybrid_enable_can_transceiver(4U, false);
  switch (mode) {
    case CAN_MODE_NORMAL:
    case CAN_MODE_OBD_CAN2:
      if ((bool)(mode == CAN_MODE_NORMAL) != (bool)(harness.status == HARNESS_STATUS_FLIPPED)) {
        // B12,B13 (BUS1O, U8): disable
        set_gpio_pullup(GPIOB, 12, PULL_NONE);
        set_gpio_mode(GPIOB, 12, MODE_ANALOG);

        set_gpio_pullup(GPIOB, 13, PULL_NONE);
        set_gpio_mode(GPIOB, 13, MODE_ANALOG);

        // B5,B6 (BUS1N, U10): FDCAN2
        set_gpio_pullup(GPIOB, 5, PULL_NONE);
        set_gpio_alternate(GPIOB, 5, GPIO_AF9_FDCAN2);

        set_gpio_pullup(GPIOB, 6, PULL_NONE);
        set_gpio_alternate(GPIOB, 6, GPIO_AF9_FDCAN2);
        hybrid_enable_can_transceiver(2U, true);
      } else {
        // B5,B6 (BUS1N, U10): disable
        set_gpio_pullup(GPIOB, 5, PULL_NONE);
        set_gpio_mode(GPIOB, 5, MODE_ANALOG);

        set_gpio_pullup(GPIOB, 6, PULL_NONE);
        set_gpio_mode(GPIOB, 6, MODE_ANALOG);

        // B12,B13 (BUS1O, U8): FDCAN2
        set_gpio_pullup(GPIOB, 12, PULL_NONE);
        set_gpio_alternate(GPIOB, 12, GPIO_AF9_FDCAN2);

        set_gpio_pullup(GPIOB, 13, PULL_NONE);
        set_gpio_alternate(GPIOB, 13, GPIO_AF9_FDCAN2);
        hybrid_enable_can_transceiver(4U, true);
      }
      break;
    default:
      break;
  }
}

static uint32_t hybrid_read_voltage_mV(void){
  // PF11 = ADC1_INP2, R3 10k / R2 1k divider from 12V_Protected
  return adc_get_mV(&(const adc_signal_t) ADC_CHANNEL_DEFAULT(ADC1, 2)) * 11U;
}

static void hybrid_set_usb_load_switch(bool enabled) {
  set_gpio_output(GPIOB, 14, !enabled);
}

static void hybrid_init(void) {
  common_init_gpio();

  // G11,B3,D7,B4: transceiver standby (STB, high = standby)
  set_gpio_pullup(GPIOG, 11, PULL_NONE);
  set_gpio_mode(GPIOG, 11, MODE_OUTPUT);

  set_gpio_pullup(GPIOB, 3, PULL_NONE);
  set_gpio_mode(GPIOB, 3, MODE_OUTPUT);

  set_gpio_pullup(GPIOD, 7, PULL_NONE);
  set_gpio_mode(GPIOD, 7, MODE_OUTPUT);

  set_gpio_pullup(GPIOB, 4, PULL_NONE);
  set_gpio_mode(GPIOB, 4, MODE_OUTPUT);

  // B1: 5VOUT_S
  set_gpio_pullup(GPIOB, 1, PULL_NONE);
  set_gpio_mode(GPIOB, 1, MODE_ANALOG);

  // B14: USB-A load switch, push-pull, port on
  set_gpio_output_type(GPIOB, 14, OUTPUT_TYPE_PUSH_PULL);
  set_gpio_pullup(GPIOB, 14, PULL_NONE);
  hybrid_set_usb_load_switch(true);
  set_gpio_mode(GPIOB, 14, MODE_OUTPUT);
}

static harness_configuration hybrid_harness_config = {
  .GPIO_SBU1 = GPIOC,
  .GPIO_SBU2 = GPIOA,
  .GPIO_relay_SBU1 = GPIOC,
  .GPIO_relay_SBU2 = GPIOC,
  .pin_SBU1 = 4,
  .pin_SBU2 = 1,
  .pin_relay_SBU1 = 10,
  .pin_relay_SBU2 = 11,
  .adc_signal_SBU1 = ADC_CHANNEL_DEFAULT(ADC1, 4),
  .adc_signal_SBU2 = ADC_CHANNEL_DEFAULT(ADC1, 17)
};

board board_hybrid = {
  .set_bootkick = unused_set_bootkick,
  .harness_config = &hybrid_harness_config,
  .has_spi = false,
  .has_fan = false,
  .avdd_mV = 3300U,
  .fan_enable_cooldown_time = 0U,
  .init = hybrid_init,
  .enable_can_transceiver = hybrid_enable_can_transceiver,
  .led_GPIO = {GPIOE, GPIOE, GPIOE},
  .led_pin = {4, 3, 2},
  .set_can_mode = hybrid_set_can_mode,
  .read_voltage_mV = hybrid_read_voltage_mV,
  .read_current_mA = unused_read_current,
  .set_fan_enabled = unused_set_fan_enabled,
  .set_ir_power = unused_set_ir_power,
  .set_siren = unused_set_siren,
  .read_som_gpio = unused_read_som_gpio,
  .set_amp_enabled = unused_set_amp_enabled
};
