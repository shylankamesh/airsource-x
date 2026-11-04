# Original Mendeley data archive

The original six-station CSV archive is not redistributed here. Download Version 1 of the [Delhi Multi-Site Air-Quality Data Set](https://doi.org/10.17632/bzhzr9b64v.1), licensed CC BY 4.0, and extract the six `*_Hourly.csv` files under:

```text
data/raw/mendeley-bzhzr9b64v/
```

Then regenerate the prepared dataset with:

```bash
python scripts/prepare_public_dataset.py
```

The script requires exactly six station files and writes the combined, hourly table to `data/processed/delhi_multisite_hourly.csv`. Attribution, preparation details, and the historical evaluation limits are documented in [`docs/DATA_PROVENANCE.md`](../../docs/DATA_PROVENANCE.md).
