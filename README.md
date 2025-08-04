# FairnessNSP: A Nurse scheduling problem (NSP) ILP optimization with a fairness constraints
This repo contains a code to build schedules for a set of agents under linear constraints, following our [paper](http://dx.doi.org/10.13140/RG.2.2.28819.90405). We recommend reading it before running the code.
The project revolves aroung the Integer Linear Programming (ILP) optimization problem formalism.
The problem is solved using the [PuLP](https://pypi.org/project/PuLP/) library.

The script is primarily intended to design schedules for a hospital service under a list of its specific constraints, but can be adapted for any similar problem.
The parameters and constraints provided correspond to a real-life case in a French hospital's service.
It enabled to ensure the compliance of the computed solutions with the expectations of the service's management.

Two sets of agents are dealt with in the repo:
- nurses (refered to with the "inf" suffix in filenames, standing for "infirmier" in French)
- caregivers (refered to with the "as" suffix in filenames, standing for "aide-soignant" in French)

The output `.xlsx` file should look like the following screenshot:
<img src="imgs/schedule_screen_example.png">


# Overview of files

## Core Files
- `scheduler_core.py`: Abstract base class for schedule optimization
- `nurse_scheduler.py`/`caregiver_scheduler.py`: Agent-specific scheduler implementations
- `config_manager.py`: Configuration management for different agent types
- `excel_export.py`: OpenPyXL functions to generate the output `.xlsx` schedule files
- `objectives.py`: PuLP objective functions for optimization criteria

## Legacy Files (Original Implementation)
- `script_inf.py`/`script_as.py`: Original scripts to build nurse/caregiver schedules
- `parameters/parametres_inf.py`/`parameters/parametres_as.py`: Parameter files for the original scripts

## Web Interface
- `streamlit_app.py`: Streamlit web interface for easy scheduling
- `start_streamlit.sh`: Startup script for the web interface
- `.streamlit/config.toml`: Streamlit configuration

## Output
- `output/nurses_schedule.xlsx`/`output/caregivers_schedule.xlsx`: Example output schedules

# Dependencies
[Pandas](https://pandas.pydata.org/), [OpenPyXL](https://openpyxl.readthedocs.io/en/stable/), [PuLP](https://pypi.org/project/PuLP/) and [Streamlit](https://streamlit.io/).

## Installation with uv (Recommended)
```bash
uv sync
```

## Installation with pip
```bash
pip install -r requirements.txt
```

# Running the code

## Web Interface (Recommended)
For the easiest experience, use the Streamlit web interface:

```bash
# Quick start
./start_streamlit.sh

# Or manually
source .venv/bin/activate
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501`

## Command Line Interface

### Refactored Version (Recommended)
```bash
# Schedule nurses
python schedule_nurses.py

# Schedule caregivers  
python schedule_caregivers.py

# Schedule both
python unified_scheduler.py
```

### Legacy Version
To run the original code and generate a nurse schedule, fill the `parameters/parametres_inf.py` file and run:
```bash
python script_inf.py
```

The logs will indicate if the problem was successfully resolved (logs will display `Optimal solution`) or if it failed (logs will display `Infeasible`).
If the program is successful, the resulting `.xlsx` file will be stored in the `output` folder.


# License and attribution
This code is made available for use under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0). You may obtain a copy of the License at: https://creativecommons.org/licenses/by-nc-sa/4.0/.


# Citation
If you use this work, consider citing our [paper available on ResearchGate: ](http://dx.doi.org/10.13140/RG.2.2.28819.90405):

```latex
@misc{https://doi.org/10.13140/rg.2.2.28819.90405,
  doi = {10.13140/RG.2.2.28819.90405},
  url = {https://rgdoi.net/10.13140/RG.2.2.28819.90405},
  author = {Chirol,  Louis and Zeroual,  Jad},
  language = {en},
  title = {Using fairness as a constraint in the Nurse scheduling problem (NSP): the case of a French hospital},
  publisher = {Unpublished},
  year = {2024}
}
```

