# Hybrid No-reference Mode 0 Reference Implementation
Hybrid No-reference Mode 0 is a short term video quality prediction model that uses full bitstream data to estimate video quality scores on a segment level.

## Requirements
To be able to run the model you need to install some software.
Currently the model is only tested on Ubuntu >= 20.04.

* python3, python3-pip, python3-venv
* poetry (e.g. pip3 install poetry)
* ffmpeg
* depencencies for the video_parser (see [bitstream_mode3_videoparser](https://github.com/Telecommunication-Telemedia-Assessment/bitstream_mode3_videoparser))

To install all requirements under Ubuntu please run the following commands:

```bash
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-numpy python3-pip git scons ffmpeg
pip3 install --user poetry
# ffmpeg/videoparser specific
sudo apt-get -y install autoconf automake build-essential libass-dev libfreetype6-dev libsdl2-dev libtheora-dev libtool libva-dev libvdpau-dev libvorbis-dev libxcb1-dev libxcb-shm0-dev libxcb-xfixes0-dev pkg-config texinfo wget zlib1g-dev yasm
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
poetry run hybrid_mode0 test_videos/test_video_h264.mkv
```

Otherwise check the included help, `poetry run hybrid_mode0 --help`:
```
usage: hybrid_mode0 [-h] [--result_folder RESULT_FOLDER] [--model MODEL] [--hybrid_model_type {1,2}] [--cpu_count CPU_COUNT]                    [--device_type {pc,tv,tablet,mobile}] [--device_resolution {3840x2160,2560x1440}]
                    [--viewing_distance {1.5xH,4xH,6xH}] [--display_size {10,32,37,5.1,5.5,5.8,55,65,75}] [--tmp TMP]
                    [--tmp_reencoded TMP_REENCODED] -br RE_ENCODING_BITRATE -vw RE_ENCODING_WIDTH -vh RE_ENCODING_HEIGHT -fr
                    RE_ENCODING_FRAMERATE [-codec RE_ENCODING_CODEC] [-d] [-nocached_features] [-cache_reencodes] [-q]
                    video [video ...]

Hybrid no-reference mode 0 video quality model reference implementation

positional arguments:
  video                 input video to estimate quality

optional arguments:
  -h, --help            show this help message and exit
  --result_folder RESULT_FOLDER
                        folder to store video quality results (default: reports)
  --model MODEL         model config file to be used for prediction (default: p1204_3/models/p1204_3/config.json)
  --hybrid_model_type {1,2}
                        applicable input values: {1,2}; two variants: (1) uses the specific codec to re-encode the video, (2)
                        uses HEVC to re-encode the video irrespective of the codec (default: 1)
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
  --tmp_reencoded TMP_REENCODED
                        temporary folder to store re-encoded video segments (default: ./tmp_reencoded)
  -br RE_ENCODING_BITRATE, --re_encoding_bitrate RE_ENCODING_BITRATE
                        bitrate to re-encode the video; supports ffmpeg style bitrate, e.g. 100k, 5M (default: None)
  -vw RE_ENCODING_WIDTH, --re_encoding_width RE_ENCODING_WIDTH
                        width to re-encode the video (default: None)
  -vh RE_ENCODING_HEIGHT, --re_encoding_height RE_ENCODING_HEIGHT
                        height to re-encode the video (default: None)
  -fr RE_ENCODING_FRAMERATE, --re_encoding_framerate RE_ENCODING_FRAMERATE
                        framerate to re-encode the video (default: None)
  -codec RE_ENCODING_CODEC, --re_encoding_codec RE_ENCODING_CODEC
                        codec to re-encode the video, if not specific mode will be set to 1 (default: None)
  -d, --debug           show debug output (default: False)
  -nocached_features    no caching of features (default: False)
  -cache_reencodes      caching reencoded videos (default: False)
  -q, --quiet           not print any output except errors (default: False)

rrao, stg7 2022

```

Most parameter default settings are for the PC/TV use case.


## Authors

Main developers:
* Rakesh Rao Ramachandra Rao - Technische Universität Ilmenau
* Steve Göring - Technische Universität Ilmenau
