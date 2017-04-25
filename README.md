# transcode2XVID
Unattended video transcoder to XVID and MP3 codecs, in AVI containers.

## What does this do?
This program transcode video files to XviD and MP3 in an AVI format. Output
files are optimized for DVD players, but compatible with devices supporting
DivX/Xvid. Subtitles are handled automatically and, if present, subtitle files
with compatible names will be created for output files or it can be hardsubbed
if the appropriate option is selected.

## How does it work?
transcode2XVID uses ffmpeg and other system tools to convert the input videos.

## How do I install it?
As a python script you can just run the transcode2XVID.py file, or put a symbolic link in any directory of your PATH (e.g. /usr/local/bin)
The script needs ffmpeg to work, so, if it can not find it in your system it will complain and exit.

## XVID, DVD, seriously?
In the time of smart TVs, blu rays and video streaming, less people are using good old, low resolution, DVD players. But, for those whose still own and use one, this script can be a very valuable tool.

## How do I use it?
Just do:
`transcode2XVID.py video_file[s]`

It has some options (type `transcode2XVID -h` or see below), but defaults should work in most cases.

### Options
```
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -q QUANTIZER, --quantizer=QUANTIZER
                        Quantizer value [default: 4]. Determines the output
                        video quality. Smaller values gives better qualities
                        and bigger file sizes, bigger values result in less
                        quality and smaller file sizes. Default value results
                        in a nice quality/size ratio. Quantizer values should
                        be in the range of 2 to 31.
  -r, --replace-original-video-file
                        If True original video files will be erased after
                        transcoding [default: False]. WARNING: deleted files
                        can not be easily recovered!
  -x FILENAME_POSTFIX, --filename-postfix=FILENAME_POSTFIX
                        Postfix to be added to newly created XviD video files
                        [default: _xvid].
  -c, --auto-crop       Autocrop output files [default: False]. WARNING: Use
                        with caution as some video files has variable width
                        horizontal (and vertical) black bars, in those cases
                        you will probably lose data.
  -s, --hardsub         If True then the corresponding subtitles will be
                        hardsubbed to videos [default: False].
```

