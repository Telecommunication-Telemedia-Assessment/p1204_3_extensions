# AVQBits – Adaptive Video Quality Model Based on Bitstream Information for Various Video Applications

This repository contains the AVQBits models from TU Ilmenau.

Contents:

- [Introduction](#introduction)
- [General Requirements](#general-requirements)
- [Acknowledgments](#acknowledgments)
- [License](#license)
- [Authors](#authors)

## Introduction

The AVQBits models come in different modes:

* [Mode 0](./bitstream_mode0/README.md): This model relies on codec, framerate, resolution, and bitrate information to determine the quality.
* [Mode 1](./bitstream_mode1/README.md): In addition to the above information, the frame types and sizes are used.
* [Hybrid No-reference Mode 0](./hybrid_mode0/README.md): Here, mode 0 information is enhanced using the (received) video stream.

The details of the usage of the individual models are described in the README of the respective models.

The listed models use [ITU-T P.1204.3](https://github.com/Telecommunication-Telemedia-Assessment/bitstream_mode3_p1204_3) internally with adaptions to other use cases. If you have access to the video bitstreams and require a high-accuracy bitstream-based model, please use P.1204.3 directly.

The proposed models were compared with state of the art models for different application scopes, and it has been shown that for all use cases, AVQBits|M3 (i.e., P.1204.3) either performs on par with or outperforms the best performing full reference model, i.e. VMAF. Although the performance of the Mode 0 and Mode 1 models varies for different use-cases, the performance of these models is better than state of the art NR models in general, and also comparable to FR models other than VMAF. For details, please see the [paper](#acknowledgments).

## General Requirements

All models have in common that they need Python 3 and [`poetry`](https://python-poetry.org/) installed.
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
