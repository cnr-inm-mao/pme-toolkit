## Backmapping configuration

Backmapping is defined through a dedicated JSON file with the following structure:

    {
      "case_json": "case.json",
      "input": {
        "file": "x01.txt",
        "format": "txt"
      },
      "reduced_space": {
        "nconf": 5
      },
      "denorm": {
        "rule": "3sigma",
        "c": 3.0
      },
      "output": {
        "file": "results/u_base.txt",
        "format": "txt",
        "layout": "col",
        "what": "Ubase",
        "write_meta": true
      }
    }

---

## Fields description

### `case_json`

Type: string  

Path to the original configuration file used to generate the model.
It is resolved relative to the backmapping JSON file. Paths under `input`,
`output` and the optional `run_case.model_file` are instead resolved relative
to the referenced fitting case directory.

This is required to:

- reconstruct normalization settings  
- recover dataset structure  

---

## Input (`input`)

Defines a single vector of normalized reduced coordinates `x01`, with every
component in `[0,1]`. The standalone workflow processes one design per call.

### Fields

- `file` (string)  
  Path to the file containing reduced coordinates

- `format` (string)  
  Input format (e.g. `"txt"`)

---

## Reduced space (`reduced_space`)

Selects how many leading modes of the saved model are used for this backmap.

### Fields

- `nconf` (int)  
  Number of reduced coordinates, between one and the model's retained
  dimension. If omitted, all retained modes are used. The input vector must
  have exactly this many entries; this field is not a sample count.

---

## Denormalization (`denorm`)

Controls how reduced variables are mapped back.

### Fields

- `rule` (string)  

    `"3sigma"` → map each normalized coordinate to
    `[-c*sqrt(lambda), +c*sqrt(lambda)]`

    `"minmax"` → map to that reduced coordinate's observed training range

- `c` (float)  

    scaling coefficient (typically 3.0)

---

## Output (`output`)

Defines output file and format.

### Fields

- `file` (string)  
  Output file path

- `format` (string)  
  Output format (e.g. `"txt"`)

- `layout` (string)  

    `"col"` → one CSV column
    `"row"` → one CSV row

    Text output always writes one value per line.

- `what` (string)

    `"Ubase"` → full reconstructed design vector in original units, with
    fixed variables reinserted at their baseline values

    `"Uact"` → active reconstructed variables in original units

    `"P"` → reconstructed augmented vector in the model's prepared coordinates

    `"alpha"` → denormalized reduced coordinates

- `write_meta` (bool)  
  Write additional metadata

---

## Notes

- the fitting run must first save `model.npz` (Python) or `model.mat` (MATLAB)
- no solver field is required here: backmapping uses the saved basis
- input reduced coordinates must match the selected `reduced_space.nconf`
- denormalization depends on the original dataset statistics  
- the backmapping process reconstructs design variables consistent with the training space  

---

## Summary

Backmapping is a **post-processing step** that maps reduced coordinates back to:

- original design variables  
- physically interpretable configurations  

using the model defined in the original case.
