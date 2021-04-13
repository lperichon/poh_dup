# poh_dup
Checks for duplicates in the Proof of Humanity registry

## Installation

### Requirements

  * macOS or Linux (Windows not officially supported, but might work)
  * Python 3.3+ or Python 2.7
  * [face_recognition library](https://github.com/ageitgey/face_recognition#installation)
## Usage

### Command-Line Interface
```bash
$ python2 poh_dup.py 0x914985a71b321aacc40e47d1c66286bc7a0e5432
Getting registration data since 13-Apr-2021 (10:39:37.000000)
...........Done!
Downloading registration photo for 0x914985a71b321aacc40e47d1c66286bc7a0e5432
Loading data for face recognition (this could take a while)
...................Done!
Checking for duplicates of https://app.proofofhumanity.id/profile/0x914985a71b321aacc40e47d1c66286bc7a0e5432 between 659 registered humans
WARNING: this profile could be duplicated! see: https://app.proofofhumanity.id/profile/0xc6f41651921f38a3343d9016dd1da5d5c18b1867
```

The results can be:

```
ALERT: this profile most likely duplicated! see: https://app.proofofhumanity.id/profile/0xc6f41651921f38a3343d9016dd1da5d5c18b1867
```

when its almost surely a duplicate and

```
WARNING: this profile could be duplicated! see: https://app.proofofhumanity.id/profile/0xc6f41651921f38a3343d9016dd1da5d5c18b1867
```

when its similar