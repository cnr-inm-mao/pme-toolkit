# Goal-oriented benchmark — PI-PME — glider

This benchmark defines a **goal-oriented dataset-selection workflow** for the **glider** case using **PI-PME**.

The workflow is specified through **JSON configuration files** and can be executed with both **MATLAB and Python implementations**.

---

## Files

- `case.json` — configuration for the dimensionality-reduction run  
- `backmapping.json` — example configuration for backmapping  

---

## Dataset

This benchmark relies on the **glider dataset** described in:

    databases/glider/

The dataset may be:

- already available locally, or  
- referenced/downloaded through the metadata defined in the repository  

---

## Workflow

Run PME:

    pme-run case.json

or

    matlab -batch "run_pme('case.json')"

Run backmapping:

    pme-back backmapping.json

or

    matlab -batch "run_back('backmapping.json')"

Outputs are written to the `outdir` specified in the JSON configuration.

---

## Notes

- This benchmark represents a **reference configuration** for the glider case  
- It is used for **testing, validation, and reproducibility**  
- The same configuration is compatible with both MATLAB and Python  
