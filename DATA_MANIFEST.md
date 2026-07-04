# Data Manifest

Raw model-capture CSVs are released separately (they are large and require API access to regenerate); this file records the SHA-256 of each frozen, immutable capture so a released dataset can be verified byte-for-byte against the analysis in this repository. Each capture is also accompanied by a machine-readable receipt in `data/frozen/`.

Generated 2026-07-04. Grid: 100 companies x 12 dates x 3 replicates = 3,600 calls per version; 7,200 per pair; 14,400 across both pairs (plus 8x3 temperature subgrids).

| file | rows | sha256 |
|---|---|---|
| `runs_gemini_flash_v_new.csv` | 3600 | `0810a786cd41e01f45d77fec8d0c23ba623ab9b80dd48db4e7346208c73ea462` |
| `runs_gemini_flash_v_new_T00.csv` | 72 | `8eab27abf148ee25267b72ca0d1573e41f03ad0f2150800922863749f2cf0b8b` |
| `runs_gemini_flash_v_new_T07.csv` | 72 | `87236b1d342fa0e2b023ee4bc360554f17f94486fc831458515a5f05821307c2` |
| `runs_gemini_flash_v_new_T10.csv` | 72 | `068ce716db160103fa13f22f75830b629e61c8a4b6352d8f51ca019d6aa56a4e` |
| `runs_gemini_flash_v_old.csv` | 3600 | `e99b948eea91a9f4cb5532926c8fad207a575dc101e0d4034713192fcbd18be0` |
| `runs_gemini_flash_v_old_T00.csv` | 72 | `94168235070472deaa95070c31f0d85d31a14eeb5bf9d3bf7a0eaf283ccc126d` |
| `runs_gemini_flash_v_old_T07.csv` | 72 | `12fcbf4b753be5a9fdea8b727866993800a3a0c2ec70833bd8e4b67bfc5e7910` |
| `runs_gemini_flash_v_old_T10.csv` | 72 | `dc0b6f352e7ecc0341b651cbceaf8731111dd985ea60ae9d3fd4d3b79a035185` |
| `runs_openai_nano_v_new.csv` | 3600 | `5eb14ff19f1fea3d653f95efa923756c17ec22f5ae1d8f6b2d85e15f3325dc03` |
| `runs_openai_nano_v_new_T00.csv` | 72 | `8aabc688f89a0b5612205f68083c72f530a7ed0283077c367d3c71dae8da12e9` |
| `runs_openai_nano_v_new_T07.csv` | 72 | `f13b68022d4ea921ec0f2a96e1e95126ef0bcb81e7e204c5aa164afd3fbe6866` |
| `runs_openai_nano_v_new_T10.csv` | 72 | `98d40280e498a0c629552aad34aa315dc6a55ed696952b8df18883835eaad031` |
| `runs_openai_nano_v_old.csv` | 3600 | `af1ace99c938a23ddba948d7df09276316e1b626ef79b64c4775cedd58c22d7d` |
| `runs_openai_nano_v_old_T00.csv` | 72 | `1bf3d56c836eae90fb2e4c8caf4e721ac3f6e79b453757512a2c7b98520c135b` |
| `runs_openai_nano_v_old_T07.csv` | 72 | `71a8cf2d6d67676c933cabdde3e78883aaf8ec606bfb20d145a04d5a56c06a8d` |
| `runs_openai_nano_v_old_T10.csv` | 72 | `2260acea700c6af86fcd838b1adc491696d2d7504cc0aa3f0a26c2b1c941b739` |

## Verifying

```
shasum -a 256 data/raw/<file>.csv   # must match the hash above
```

The pre-registration freeze is separately hashed in `PREREGISTRATION.freeze.txt`.
