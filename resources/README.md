# resources: the material the figures are built from

Everyone who installs steelfig gets this folder, so a figure made on one machine can be rebuilt on another.
Drop files into the subfolder that fits; the tool and the skill look here automatically.

| folder | what goes in | how it is used |
|---|---|---|
| `catalogues/` | section tables as CSV with the same columns as `steelfig/data/*.csv` (another manufacturer, another grade, a newer edition); manufacturer excerpts as Markdown | CSVs are loaded with the built-in tables (`steelfig sections` sees them); excerpts are sources for `docs/details/` |
| `details/` | standard connection details you are allowed to share: notes, sketches, your own drawings (PDF, PNG, DXF, Markdown) | the skill reads them when it needs a rule; cite them in the rationale |
| `models/` | analysis models to draw from: Microstran `.arc`, `nodes.csv` + `members.csv` | scenes reference them as `path = "res:models/<file>"` |
| `styles/` | style sheets (`*.toml`, start from `steelfig/styles/default.toml`) for other reports or courses | `style = "<name>"` in a scene finds them here too |
| `local/` | **not committed**: copyrighted standards, drawings you may not redistribute, anything private | same uses, but stays on your machine |

Keep the file names descriptive (`stramit-cz-purlins-2024.csv`, `sci-p398-moment-joints.pdf`). `steelfig resources`
lists what is here.
