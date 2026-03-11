# nudelo

This Python module implements round path stroking ("noodling")
for `kurbopy` `BezPath` objects. It currently exports one function,
`noodle`:

```python
from nudelo import noodle
from kurbopy import BezPath
f = ufoLib2.Font("tests/data/Scurve.ufo")
paths = BezPath.from_drawable(f["A"])

new_paths = []
for path in paths:
    new_paths.extend(noodle(path, width=50, start_cap="butt", end_cap="round"))
  
```

This may also be used as a fontmake command line plugin:

```
fontmake --filter 'nudelo::NoodleFilter(pre=True,Width=50)' -u OpenPaths.ufo -o ttf
```

Or by adding a lib key into the UFO file's `lib.plist` file:

```xml
    <key>com.github.googlei18n.ufo2ft.filters</key>
    <array>
      <dict>
        <key>name</key>
        <string>nudelo.NoodleFilter</string>
        <key>pre</key>
        <true/>
        <key>kwargs</key>
        <dict>
            <key>Width</key>
            <integer>50</integer>
            <key>StartCap</key>
            <string>square</string>
            <key>EndCap</key>
            <string>square</string>
            <key>JoinType</key>
            <string>mitre</string>
            <key>RemoveExternal</key>
            <true/>
        </dict>
      </dict>
    </array>
```

The name "nudelo" is the Esperanto for "noodle".

## License

Apache 2.
