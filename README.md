# HospitalShift: A Nurse shift problem (NSP) LP optimization
This repo contains a code to build schedules for a set of agents under linear constraints.
It uses a Linear Programming optimization problem formalism.
The problem is solved using the [PuLP](https://pypi.org/project/PuLP/) library.

The script is primarily intended to design schedules for a hospital service, but can be adapted for any similar problem.
The parameters and constraints provided correspond to a real-life case in a French hospital's service.
It enabled to ensure the compliance of the computed solutions with the expectations of the service's management.

Two sets of agents are dealt with in the repo:
- nurses (refered to with the "inf" suffix in filenames, standing for "infirmier" in French)
- caregivers (refered to with the "as" suffix in filenames, standing for "aide-soignant" in French)


# Overview of files


# Installation


# Running the code


# Results


# License and attribution
This code is made available for use under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0). You may obtain a copy of the License at: https://creativecommons.org/licenses/by-nc-sa/4.0/.


# Citation
If you use this work, consider citing our [paper](https://overleaf.com):

```latex
@article{chriol_zeroual_nsp,
      title={Nurse shift problem (NSP) LP optimization},
      author={Louis Chirol and Jad Zeroual},
      year={2024},
    %   eprint={2212.12794},
    %   archivePrefix={arXiv},
    %   primaryClass={cs.LG}
}
```

