# Bitstream Mode 1 Reference Implementation
Bitstream Mode 1 is a short term video quality prediction model that uses full bitstream data to estimate video quality scores on a segment level.

## Requirements
To be able to run the model you need to install some software.
Currently the model is only tested on Ubuntu >= 20.04.

* python3, python3-pip, python3-venv
* poetry (e.g. pip3 install poetry)
* ffmpeg

To install all requirements under Ubuntu please run the following commands:

```bash
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-numpy python3-pip git ffmpeg
pip3 install --user poetry
```

After cloning this repository and installation of all requirements, run the following command:

```bash
poetry install
```

If you have problems with pip and poetry, run `pip3 install --user -U pip`.

## Input Data and Scope

As input to the model you need an encoded video sequence of short duration, e.g. 8-10s, e.g. checkout the `test_videos` folder.
H.264, H.265 or VP9 are supported video codecs of the input video sequence.
For example the [AVT-VQDB-UHD-1](https://github.com/Telecommunication-Telemedia-Assessment/AVT-VQDB-UHD-1) can be used to validate the model performance, as it is shown in the paper `rao2020p1204`.

## Usage
To use the provided tool, e.g. run
```bash
poetry run bitstream_mode1 test_videos/test_video_h264.mkv
```

Otherwise check the included help, `poetry run bitstream_mode1 --help`:
```
usage: bitstream_mode1 [-h] [--result_folder RESULT_FOLDER] [--model MODEL] 
                [--cpu_count CPU_COUNT] [--device_type {pc,tv,tablet,mobile}] 
                [--device_resolution {3840x2160,2560x1440}]
                [--viewing_distance {1.5xH,4xH,6xH}] 
                [--display_size {10,32,37,5.1,5.5,5.8,55,65,75}] [--tmp TMP]
                video [video ...]

Bitstream mode 1 video quality model reference implementation

positional arguments:
  video                 input video to estimate quality

optional arguments:
  -h, --help            show this help message and exit
  --result_folder RESULT_FOLDER
                        folder to store video quality results (default: reports)
  --model MODEL         model config file to be used for prediction (default: /home/rakesh/work/p1204_3_advanced_applications/
                        bitstream_mode1/bitstream_mode1/models/bitstream_mode1/config.json)
  --cpu_count CPU_COUNT
                        thread/cpu count (default: 40)
  --device_type {pc,tv,tablet,mobile}
                        device that is used for playout (default: pc)
  --device_resolution {3840x2160,2560x1440}
                        resolution of the output device (width x height) (default: 3840x2160)
  --viewing_distance {1.5xH,4xH,6xH}
                        viewing distance relative to the display height (default: 1.5xH)
  --display_size {10,32,37,5.1,5.5,5.8,55,65,75}
                        display diagonal size in inches (default: 55)
  --tmp TMP             temporary folder to store bitstream stats and other intermediate results (default: ./tmp)

rrao, stg7 2021

```

Most parameter default settings are for the PC/TV use case.