# Home Assistant for mornin'

Home Assistant platform for Mornin'+.

It supports `cover` component and can be used to open / close the curtain on your home.


----


## Notice and Limitations

* This is UNOFFICIAL project for the personal convenience of IoT lovers.

    * I don't have any relationship with the vendor company (Robit Inc.) of the mornin'. Also, "mornin'" and "mornin'+" is a trademark of their. Thank you for the nice product!

* This software has some limitations and is unstable, because it published under the TESTING phase.

    * I tested on Hass.io 0.92.2.

    * In currently, this software only supports mornin'+ (mornin plus).

* I don't any guarantee about this project.


----


## Get Started

### 0. Finish the setup of mornin'+

First, you need to finish the setup process of your mornin'+ as normally.

### 1. Get the key of mornin'+

You can get it from the Android app.

HINT: `D AuthRepository: Encrypt key: <xxxxxxxx xxxxxxxx xxxxxxxx xxxxxxxx>`

### 2. Install the component to Home Assistant

On Your Home Assistant server (Hass.io):
```
# cd /config

# wget https://github.com/mugifly/homeassistant-mornin/archive/master.zip

# unzip master.zip
# rm master.zip

# cp -r homeassistant-mornin-master/custom_components/ /config/
# rm -rf homeassistant-mornin-master/
```

### 3. Make a configuration

In `configuration.yaml`:
```
cover:
  - platform: mornin
    api_key: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    mac: 'xx:xx:xx:xx:xx:xx'
    name: 'Curtain of Living'
```

* `platform` (Required) - It must be `mornin`.

* `api_key` (Required) - Encrypt key (alphanumeric) of your mornin+. Don't include spaces.

* `mac` (Required) - MAC address of your mornin+.

* `name` (Optional) - Name of your mornin+. In typically it should be name of curtain.

### 4. Restart Home Assistant

After restarting, your mornin'+ will be appeared as Cover on your Home Assistant.

Let's enjoy IoT life :)


----

## FAQ

### How to check the debug log

Firstly, you need to specifying the log level for this component, in configuration.yaml on Home Assistant.

```
logger:
  default: warning
  logs:
    custom_components.mornin.cover: debug
```

After saving and restarting, then open the "Info" page of your Home Assistant (http://example.com/dev-info) on the browser, and click the "LOAD FULL HOME ASSISTANT LOG" button.


----


## License and Thanks

```
The MIT License (MIT)
Copyright (c) 2019 Masanori Ohgita
```

And thank you for mornin'
