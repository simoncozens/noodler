# noodler-py

This Python module implements round path stroking ("noodling")
for `kurbopy` `BezPath` objects. It currently exports one function,
`noodle`:

```python
from noodler import noodle
from kurbopy import BezPath
f = ufoLib2.Font("tests/data/Scurve.ufo")
paths = BezPath.from_drawable(f["A"])

new_paths = []
for path in paths:
    new_paths.extend(noodle(path, width=50, start_cap="butt", end_cap="round"))
  
```

This modifies the glyph in place. The library works with defcon and ufoLib2
objects.

This may also be used as a fontmake command line plugin:

```
fontmake --filter 'noodler::NoodleFilter(pre=True,Width=50)' -u OpenPaths.ufo -o ttf
```

Or by adding a lib key into the UFO file's `lib.plist` file:

```xml
    <key>com.github.googlei18n.ufo2ft.filters</key>
    <array>
      <dict>
        <key>name</key>
        <string>noodler.NoodleFilter</string>
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

## Building

Use `maturin` to build `noodler`.

```
pip3 install maturin
python3 -m venv strokervenv
. ./strokervenv/bin/activate
maturin develop
maturin build # Build wheel
```

## License

Apache 2.
