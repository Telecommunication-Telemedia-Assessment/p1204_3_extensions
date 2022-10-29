# P.1204.3 Extensions

This repository contains the P.1204.3 extended models: Mode0, Mode1, Hybrid No-reference Mode 0 (HYN0). The details of the usage of the individual models are described in the README of the respective models which are listed below:

* [Mode 0](./bitstream_mode0/README.md)
* [Mode 1](./bitstream_mode1/README.md)
* [Hybrid No-reference Mode 0](./hybrid_mode0/README.md)

The listed models use [ITU-T P.1204.3](https://github.com/Telecommunication-Telemedia-Assessment/bitstream_mode3_p1204_3) internally with adaptions to other use cases.


## General Requirements

All models have in common that they need Python 3 and [poetry](https://python-poetry.org/) installed.
The code is tested for Linux (Ubuntu >=20.04).
Check the specific README files of each of the models for other dependencies.


## Acknowledgments
If you use this software in your research, please include a link to the repository and reference one of the following paper.

```
@ARTICLE{rao2022p1204extensions,
  author={Ramachandra Rao, Rakesh Rao and Göring, Steve and Raake, Alexander},
  journal={IEEE Access}, 
  title={AVQBits—Adaptive Video Quality Model Based on Bitstream Information for Various Video Applications}, 
  year={2022},
  volume={10},
  number={},
  pages={80321-80351},
  doi={10.1109/ACCESS.2022.3195527}
}

@inproceedings{rao2020p1204,
  author={Rakesh Rao {Ramachandra Rao} and Steve G\"oring and Werner Robitza and Alexander Raake and Bernhard Feiten and Peter List and Ulf Wüstenhagen},
  title={Bitstream-based Model Standard for 4K/UHD: ITU-T P.1204.3 -- Model Details, Evaluation, Analysis and Open Source Implementation},
  BOOKTITLE={2020 Twelfth International Conference on Quality of Multimedia Experience (QoMEX)},
  address="Athlone, Ireland",
  days=26,
  month=May,
  year=2020,
}
```

## License
GNU General Public License v3. See [LICENSE](LICENSE) file in this repository.


## Authors

Main developers:
* Rakesh Rao Ramachandra Rao - Technische Universität Ilmenau
* Steve Göring - Technische Universität Ilmenau
