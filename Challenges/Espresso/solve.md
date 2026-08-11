Vedem dupa ce rulam un strings pe .bin ca este folosita o placuta esp32.
```
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
4096          0x1000          ESP Image (ESP32): segment count: 3, flash mode: DIO, flash speed: 40MHz, flash size: 4MB, entry address: 0x40080644, hash: sha256
32768         0x8000          ESP32 Partition Table Entry: label: "nvs", type: DATA, subtype: NVS, offset: 0x9000, size: 0x6000, flags: 0x0 (not encrypted)
32800         0x8020          ESP32 Partition Table Entry: label: "phy_init", type: DATA, subtype: PHY/RF, offset: 0xf000, size: 0x1000, flags: 0x0 (not encrypted)
32832         0x8040          ESP32 Partition Table Entry: label: "factory", type: APP, subtype: Factory/OTA DATA, offset: 0x10000, size: 0x100000, flags: 0x0 (not encrypted)
65536         0x10000         ESP Image (ESP32): segment count: 6, flash mode: DIO, flash speed: 40MHz, flash size: 2MB, entry address: 0x400814ac, hash: sha256
65824         0x10120         Unix path: /dev/uart/0
```
Vedem ca avem imaginea de la adresa 0x10000.
Deci o extragem cu dd
```
dd if=firmware.bin of=factory_app.bin bs=1 skip=$((0x10000)) count=$((0x100000))
```

Si dupa o analizam cu esptool

```
esptool image_info factory_app.bin 
esptool v5.3.1
Image size: 1048576 bytes
Detected image type: ESP32

ESP32 Image Header
==================
Image version: 1
Entry point: 0x400814ac
Segments: 6
Flash size: 2MB
Flash freq: 40m
Flash mode: DIO

ESP32 Extended Image Header
===========================
WP pin: 0xee (disabled)
Flash pins drive settings: clk_drv: 0x0, q_drv: 0x0, d_drv: 0x0, cs0_drv: 0x0, hd_drv: 0x0, wp_drv: 0x0
Chip ID: 0 (ESP32)
Minimal chip revision: v0.0, (legacy min_rev = 0)
Maximal chip revision: v3.99

Segments Information
====================
Segment   Length   Load addr   File offs  Memory types
-------  -------  ----------  ----------  ------------
      0  0x08b68  0x3f400020  0x00000018  DROM
      1  0x02a6c  0x3ffb0000  0x00008b88  BYTE_ACCESSIBLE, DRAM
      2  0x04a14  0x40080000  0x0000b5fc  IRAM
      3  0x0c7b8  0x400d0020  0x00010018  IROM
      4  0x060f4  0x40084a14  0x0001c7d8  IRAM
      5  0x00028  0x50000000  0x000228d4  RTC_DATA

ESP32 Image Footer
==================
Checksum: 0x59 (valid)
Validation hash: 5144c340c0a97795f7fc6f06143b6c8ac914727c4a511f164a77fb022fb38e99 (valid)

Application Information
=======================
Project name: espresso
App version: 2c1ec8fd-dirty
Compile time: Feb 28 2026 03:10:39
ELF file SHA256: 58a811cbe3344dd02cc29da28c1bbd5520d152cc2bc76d61401122ca0031143d
ESP-IDF: v6.1-dev-2748-g490691bc61
Minimal eFuse block revision: 0.0
Maximal eFuse block revision: 0.99
MMU page size: 64 KB
Secure version: 0
```



