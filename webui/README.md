# insigh.io device configurator

A Vue 3 configurator served by the device. It guides users through network,
credentials, measurements, timing, review, and application of device settings.
Device requests target `http://192.168.4.1`; connect to the device's network when
testing against hardware. The Vite server provides the UI only, not a device API.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

### UI and accessibility checks

Loading spinners loop at their original speed while visible, including when the
system's reduced-motion preference is enabled. Reduced motion shortens UI
transitions and disables smooth scrolling without overriding loading animations.

The layout supports desktop and mobile browsers without external fonts or a
component framework. Shared responsive styles live in
[responsive.css](src/assets/css/responsive.css), loaded after Spectre.

- Check 320px and 375px phones, a 768px tablet, and a 1440px desktop.
  Forms should fit without page-level horizontal scrolling.
  Wide sensor and measurement-naming tables scroll within their own labeled,
  keyboard-focusable regions instead of squeezing editable fields.
  Enviro and Advind sensor tables have labeled add buttons and row counts above
  the scroll area, so adding sensors never requires horizontal scrolling.
  SDI12 add buttons remain disabled at the existing limit of 10 sensors.
- Desktop shows the full step list; phones show the current step and count.
  Satellite configurations omit the unused credentials step. Progress indicators
  are informational, so they cannot bypass step validation.
- Use only the keyboard to sign in, select network technology, choose a shield
  and timing mode, open advanced sections, and expand field help.
- Check that the selected network updates immediately, and that scanning for
  WiFi reports errors and allows selecting an SSID with the keyboard.
- Open device actions with the keyboard. Escape closes the action panel and
  restores focus. Confirmation and upload dialogs keep Tab focus inside and
  support Escape when no operation is running.
- Test incorrect credentials, disconnected-device errors, and a failed
  configuration save. Errors should be visible, and failed saves should allow
  retrying without discarding settings.
- On hardware, complete the wizard and confirm saved values and reboot behavior.
  Only apply, import, reset, or upload firmware to a device intended for testing.

`npm run build` generates the production assets, including compressed versions.
Check the production preview (`npm run preview`) as well as development mode:
production CSS is purged, including dynamically generated grid classes.
