# Detail knowledge: how each connection is built and why

One file per connection type. Each states the parts, the placement rules with numbers, the sources, and the
assumptions still to be verified. The generators in `blender/connections.py` and `blender/assembly.py` follow
these files, and the rationale they write cites them. When a rule is confirmed against a document, update the
file (source, date, who checked), then the generator's `rationale` source key, so the ASSUMPTION count only
goes down. Nothing in a generator should contradict its file.

Sources are listed in `SOURCES.md`: standards, SCI design guides and manufacturers' documents only.
