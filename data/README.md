# Hillstrom email experiment data

Kevin Hillstrom of MineThatData released this three-arm challenge in March 2008. There is one row per assigned customer, covering 64,000 customers who had purchased within the preceding year. Outcomes cover the two weeks after assignment. The arm labels denote the merchandise in the creative. Customer gender is not recorded.

[Original challenge](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) · [Publisher CSV](https://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv) · [scikit-uplift data dictionary](https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html)

## File identity

| Property | Value |
|---|---|
| Local path | `data/raw/hillstrom.csv` |
| Shape | 64,000 records × 12 fields |
| Original CSV size | 3,964,977 bytes with CRLF line endings |
| SHA-256 | `0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece` |
| Independent fingerprint | [TensorFlow Datasets checksum manifest](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/recommendation/hillstrom/checksums.tsv) |
| Pinned fallback | [CSV mirror at commit ea030d8](https://raw.githubusercontent.com/W-Tran/uplift-modelling/ea030d860f334485930d4eb5603bdbb02616dc8e/data/hillstrom/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv) |

The loader first uses an existing local file, then the publisher URL, then the pinned mirror. It normalizes line endings to CRLF before checking the hash. The bundled copy came from the pinned mirror and matches the publisher-file fingerprint after that normalization. A changed local file produces an error and is preserved.

## Dictionary

| CSV field | Meaning | Timing |
|---|---|---|
| `recency` | Months since the customer's last purchase | Pre-assignment |
| `history_segment` | Spending band in the preceding year | Pre-assignment |
| `history` | Dollar amount spent in the preceding year | Pre-assignment |
| `mens` | Indicator of prior men's-merchandise purchases | Pre-assignment |
| `womens` | Indicator of prior women's-merchandise purchases | Pre-assignment |
| `zip_code` | Area category such as urban or rural, rather than a postal identifier | Pre-assignment |
| `newbie` | New-customer indicator used by the challenge | Pre-assignment |
| `channel` | Historical purchase channel | Pre-assignment |
| `segment` | Random assignment: Mens E-Mail, Womens E-Mail or No E-Mail | Assignment |
| `visit` | Indicator of a website visit | Two-week outcome |
| `conversion` | Indicator of a purchase | Two-week outcome, primary |
| `spend` | Dollars spent by the assigned customer, including zeros | Two-week outcome, secondary |

The analysis database projects the assignment and three outcomes from the complete raw file. Spending is stored in integer cents until display. The generated row number records file order for auditing. Customers with identical observed values remain separate observations.

## Sharing the repository

The original challenge makes the CSV available for analysis. I did not locate a separate redistribution licence in the publisher's challenge materials. The local raw file is therefore ignored by Git. Publish the code, notebook and aggregate reports; readers can recreate the row-level input from its source using the runner. The third-party data is attributed to Kevin Hillstrom / MineThatData.
