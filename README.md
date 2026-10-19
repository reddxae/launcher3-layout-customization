# Layout customization

## About

Overrides the home screen grid through [Launcher3's partner resources](https://android.googlesource.com/platform/packages/apps/Launcher3/+/refs/heads/main/src/com/android/launcher3/util/Partner.java). Works with Launcher3-based launchers, like LineageOS Trebuchet and many others.

## Installation

Download the module with the desired layout from [Releases](https://github.com/reddxae/launcher3-layout-customization/releases/latest), flash it, and reboot.

## Set your own values and build

Requires Python 3.11+, Java and zipalign. Other Android build tools are downloaded automatically.

Manually set `grid_num_columns` and `grid_num_rows` in [config.xml](./src/main/res/values/config.xml), and then run:

```sh
python3 build.py
```

This builds a signed APK at `output/Launcher3PartnerLayout.apk`.

The default signing key is public. To use your keystore, run `python3 build.py --ks /path/to/your.keystore --ks-key-alias ALIAS_NAME`; passwords are prompted.
