* install on a Raspberry Pi 4B with RaspiOS Bullseye lite 32bit
* install [blinka](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) 
*  in `/boot/config.txt`, add/enable the following
    *  `dtparam=i2c_arm=on`
    *  `dtparam=spi=on`
    *  `camera_auto_detect=1`
    *  `display_auto_detect=1`
    *  `display_rotate=1`
    *  `dtoverlay=vc4-kms-v3d`
    *  `max_framebuffers=2`
    *  `disable_overscan=1`
    *  `[cm4]`
    *  `otg_mode=1`
    *  `[all]`
    *  `enable_uart=1`
    *  `dtoverlay=dwc2`
    *  `dtoverlay=spi1-3cs`
* in `/boot/cmdline.txt`, add  `modules-load=dwc2,g_cdc` after `rootwait`
  * (`g_cdc` gives `g_ether` and `g_serial` at the same time)
* connect to PC via USB-C
* ssh into `pi.local`
* `sudo raspi-config` -> name mmplex
* install Adafruit Blinka to use Circuitpython devices drivers
* rotate display
* `sudo reboot`
* ssh into `mmplex.local`
* if no COM port appears, locate USB compound device in device manager and install Microsoft USB Serial Port driver
* serial port available as `/dev/ttyGS0`

* connections
  * spi0 : SPIx(0, 0) : /dev/spidev0.0
    * SCK:GPIO#11 p23, 
    * MOSI:GPIO#10 p19, 
    * MISO:GPIO#09 p21, 
    * (CS0:GPIO#08 p24 - don't use)
    * CS: GPIO#22
  * spi1 : SPIx(1, 0) : /dev/spidev1.0 
    * SCK:GPIO#21 p40, 
    * MOSI:GPIO#20 p38, 
    * MISO:GPIO#19 p35, 
    * (CS0:GPIO#18 p12 - don't use)
    * CS : GPIO#26
  * i2c0
    * SDA
    * SCL
  * i2c1
    * SDA:p3
    * SCL:p5
   