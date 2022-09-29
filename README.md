# Heat pump controller development

Scripts for control of a 5kW EcoDan with FTC2 control unit.

These run on a RaspberryPi connected to a board with a number of solid state relays controlling the volt-free inputs on the FTC2 unit and a DAC converter to set the flow temperature.

This work is early development and I would not recommend using these scripts yet :)


### Hard code USB port used for Ecodan CN105 interface:

Find vendor id, copy contents of first line e.g '10c4'

    udevadm info -a -p  $(udevadm info -q path -n /dev/ttyUSB0) | grep idVendor
    
Find product id, copy contents of first line e.g 'ea60'

    udevadm info -a -p  $(udevadm info -q path -n /dev/ttyUSB0) | grep idProduct
    
Create rules file:

    sudo nano /etc/udev/rules.d/99-usb-serial.rules

Enter config with vendor and product id's found above, e.g:

    SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ecodan"

Save exit and then load the configuration with:

    sudo udevadm trigger
