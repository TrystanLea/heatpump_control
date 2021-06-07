#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# ---------------------------------------------------------
# Install services
# ---------------------------------------------------------
for service in "hpctrl_io" "pub_hpctrl_mode" "hpctrl"; do

    if [ -f /lib/systemd/system/$service.service ]; then
        echo "- reinstalling $service.service"
        sudo systemctl stop $service.service
        sudo systemctl disable $service.service
        sudo rm /lib/systemd/system/$service.service
    else
        echo "- installing $service.service"
    fi

    sudo cp $DIR/$service.service /lib/systemd/system

    sudo systemctl enable $service.service
    sudo systemctl restart $service.service

    state=$(systemctl show $service | grep ActiveState)
    echo "- Service $state"

done
# ---------------------------------------------------------
