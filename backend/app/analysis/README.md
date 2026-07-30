# Overview
This sub project aims to simplify comparision coral colonies in the context of marine conservation. Users can segment photos taken of a coral colony. The application will identify coral colony segments produce cropped, masked squared images. Additionally, users can generate reports of any two images (of the same colony). These reports contain LAB metrics (eg. Lightness percentiles, mean and median), color distribution graph, sobel gradient and laplacian response graphs among other metrics.

## Getting Started
### Python Environment Setup
```
# Install dependencies - this takes a while
$ cd backend
$ conda env create -f environment.yaml
$ pip install -r requirements.txt
$ conda activate coral-matcher
```

### Mask and Crop Images
The following will produce 0-n cropped images each with one found segment on black background. Depending on configuration of CoralSCOP, there are more or less images produced. For convenience the script takes a whole directory to process images for.
```
$ cd backend
$ python -m app.scripts.mass_mask_crop --input_directory ~/coral-images/directory-with-coral-images/ --output_directory ~/coral-images/processed/
```

### Produce Reports
The following will produce a directory with images and a ```report.html``` which will show all metrics and produced images for comparision of the two given images.
```
python -m app.analysis.analyze ~/coral-images/processed/cropped-coral-week-1.jpg ~/coral-images/processed/cropped-coral-week-2.jpg ~/coral-images/processed/report/
```


## Acknowledgements

### CoralSCOP
This project uses CoralSCOP, developed by Wong et al., for coral segmentation. It has proven to be extremely helpful for this project. CoralSCOP has been cloned and its code is accessed under backend/third_party.

CoralSCOP:
https://github.com/zhengziqiang/CoralSCOP

Paper:
CoralSCOP-LAT: Labeling and Analyzing Tool for Coral Reef Images with Dense Mask

Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0):
https://creativecommons.org/licenses/by-nc-sa/4.0/

This sub project integrates CoralSCOP as a preprocessing step for coral segmentation to mask and crop images. The only modifications have been made to integrate the model into this application (eg. adjusting imports and adding log statements for debugging purposes).

