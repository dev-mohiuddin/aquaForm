# AquaForm Single Integrated Soap Recycler

This project contains one compact, hook-on soap recycling machine generated
from a CadQuery source. The current active assembly is one physical housing;
the older side-base study remains only as source history and is not exported.

## Active Machine

Approximate overall size: `154 x 90 x 216 mm`.

The single housing contains:

- Top soap input and removable mesh basket
- Hinged vented cover and basket grip
- Drain perforations, isolated water gutter, and bottom drain nozzle
- Internal transfer gate and chute
- Regular and mini interchangeable MoldPod positions
- Sealed heater and thermal firewall
- Press plate, press stem, and cooling vents
- Integrated dry battery bay with four D-cell placeholders and copper contacts
- USB-C/low-voltage input placeholder
- Bottom output drawer and finished recycled soap bar
- Bathtub/shower hooks and status light

## Recycling Cycle

1. Collect small unused soap pieces in the top basket.
2. Drain excess water through the isolated gutter and bottom outlet.
3. Air-dry the pieces under the vented cover.
4. Confirm a dry batch before opening the transfer gate.
5. Guide the dry pieces through the internal chute.
6. Load the regular or mini MoldPod inside the same machine.
7. Soften the batch with the sealed low-voltage heater concept.
8. Press the softened mass into the bar form.
9. Cool and set the formed bar with lower-vent airflow.
10. Pull the bottom drawer and release the new recycled soap bar.

The machine is a visual engineering concept. Real soap formulation, heat
control, electrical isolation, waterproofing, materials, cleaning, and
certification must be validated before manufacturing. Four D cells are shown
as control/actuation placeholders, not as a claim that they can safely power a
wet soap heater directly.

## Shapr3D

Import [soap_recycler_prototype_2A.step](soap_recycler_prototype_2A.step) into
Shapr3D. STEP is the editable CAD deliverable. STL is for mesh preview or
printing reference. Shapr3D does not run `.scad` files directly.

## HTML Demo

Open [soap_recycler_demo_2A.html](soap_recycler_demo_2A.html) in a modern
browser.

- `STEP Match` shows one centered machine with zero presentation offsets.
- `Exploded` separates related internal parts without creating another device.
- `Section View`, `Battery`, `Heater`, and `Drain Path` reveal focused internals.
- `Tub mount` keeps the machine's normal titanium colors and only highlights hooks.
- The bottom timeline contains ten animated visual stages from Collect to Release.
- `Play cycle` runs the continuous sequence; sound starts only after user interaction.
- The transparent process view reveals drainage, airflow, transfer, softening, press, cooling, and output.
- Drag to orbit, scroll or use `Zoom +` / `Zoom -`, and use `Reset` or `Labels on/off` as needed.

## Regenerate

```bash
./.venv/bin/python soap_recycler_cadquery_2A.py
```

This overwrites the three main deliverables:

```text
soap_recycler_prototype_2A.step
soap_recycler_prototype_2A.stl
soap_recycler_demo_2A.html
```

The `.scad` file is retained only as a legacy OpenSCAD reference.
