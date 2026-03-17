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

This is required to:

- reconstruct normalization settings  
- recover dataset structure  

---

## Input (`input`)

Defines the reduced coordinates.

### Fields

- `file` (string)  
  Path to the file containing reduced coordinates

- `format` (string)  
  Input format (e.g. `"txt"`)

---

## Reduced space (`reduced_space`)

Defines how many configurations are processed.

### Fields

- `nconf` (int)  
  Number of configurations to backmap

---

## Denormalization (`denorm`)

Controls how reduced variables are mapped back.

### Fields

- `rule` (string)  

    `"3sigma"` → scaling based on standard deviation

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

    `"col"` → column-wise output  
    `"row"` → row-wise output  

- `what` (string)

    `"Ubase"` → reconstructed baseline variables  

- `write_meta` (bool)  
  Write additional metadata

---

## Notes

- input reduced coordinates must match the dimensionality of the trained model  
- denormalization depends on the original dataset statistics  
- the backmapping process reconstructs design variables consistent with the training space  

---

## Summary

Backmapping is a **post-processing step** that maps reduced coordinates back to:

- original design variables  
- physically interpretable configurations  

using the model defined in the original case.
