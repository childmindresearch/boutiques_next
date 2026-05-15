# `bosh example`

Generate a sample invocation JSON for a descriptor.

```sh
bosh example <descriptor> [--complete]
```

By default only the **required** inputs are filled in. With `--complete`,
optional inputs are filled in too — useful for visualising the maximal
command-line.

`Flag` inputs are treated as effectively optional regardless of their
declared `optional` field — at the runtime layer, a flag's absence is
indistinguishable from `value: false`, so a minimum example omits all
flags. `--complete` includes them.

## Example

```sh
$ bosh example fsl_bet.json
{
  "infile": "/path/to/infile",
  "maskfile": "example_maskfile"
}
```

```sh
$ bosh example fsl_bet.json --complete
{
  "infile": "/path/to/infile",
  "maskfile": "example_maskfile",
  "fractional_intensity": 0.0,
  "vg_fractional_intensity": -1.0,
  "center_of_gravity": [0.0, 0.0, 0.0],
  "overlay_flag": true,
  ...
}
```

## How values are picked

For each input, the example generator chooses a value in this order:

1. The input's declared `default-value`, if present.
2. The first entry of `value-choices`, if present.
3. The minimum of a numeric range (`minimum`) if set.
4. A typed placeholder: `0` / `0.0` for numbers, `true` for flags,
   `/path/to/<id>` for files, `example_<id>` for strings.

List inputs return `min-list-entries` copies of the chosen value (at
least one).

Sub-command unions pick the first candidate and include its `id` as the
discriminator.

## Python equivalent

```python
from boutiques import load
from boutiques.example import generate

descriptor = load("fsl_bet.json")
invocation = generate(descriptor, complete=False)
```
